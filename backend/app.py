# C:\llm_service\backend\app.py (已修正版本)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import json
import os
import sys
import logging

# 添加 LLM 服務路徑
# 確保 llm_service.py 和 app.py 在同一個 backend 目錄下
sys.path.append(os.path.dirname(__file__))

from llm_service import LLMService

# 初始化 Flask 應用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# 啟用 CORS
CORS(app)

# 資料庫配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///llm_service.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化資料庫
db = SQLAlchemy(app)

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化 LLM 服務
llm_service = LLMService()

# --- 資料庫模型 ---

class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # 關聯到訊息
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_messages=False):
        result = {
            'id': self.id,
            'session_id': self.session_id,
            'title': self.title or self.get_auto_title(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'message_count': len(self.messages)
        }
        
        if include_messages:
            result['messages'] = [msg.to_dict() for msg in self.messages]
            
        return result
    
    def get_auto_title(self):
        """自動生成對話標題"""
        if self.title:
            return self.title
        
        # 從第一條用戶訊息生成標題
        first_user_message = next((msg for msg in self.messages if msg.role == 'user'), None)
        if first_user_message:
            content = first_user_message.content[:30]
            return content + "..." if len(first_user_message.content) > 30 else content
        
        return f"對話 {self.created_at.strftime('%m-%d %H:%M')}"

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    # --- [已修正] 將 'metadata' 欄位名稱更改為 'message_metadata' ---
    message_metadata = db.Column(db.Text, nullable=True)  # JSON 字串
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'role': self.role,
            'content': self.content,
            # --- [已修正] 從 'message_metadata' 讀取 ---
            'metadata': json.loads(self.message_metadata) if self.message_metadata else {},
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def set_metadata(self, metadata_dict):
        """設定元數據"""
        # --- [已修正] 存入 'message_metadata' ---
        self.message_metadata = json.dumps(metadata_dict, ensure_ascii=False)
    
    def get_metadata(self):
        """獲取元數據"""
        # --- [已修正] 從 'message_metadata' 讀取 ---
        return json.loads(self.message_metadata) if self.message_metadata else {}

# --- API 路由 ---

@app.route('/api/chat', methods=['POST'])
def chat():
    """主要的聊天 API"""
    try:
        data = request.get_json()
        
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not user_message:
            return jsonify({'error': '訊息不能為空'}), 400
        
        # 獲取或創建對話
        conversation = None
        if session_id:
            conversation = Conversation.query.filter_by(session_id=session_id, is_active=True).first()
        
        if not conversation:
            conversation = Conversation()
            db.session.add(conversation)
            db.session.flush()  # 獲取 ID
        
        # 儲存用戶訊息
        user_msg = Message(
            conversation_id=conversation.id,
            role='user',
            content=user_message
        )
        db.session.add(user_msg)
        
        # 獲取對話歷史
        conversation_history = []
        # [修正] 獲取完整的對話歷史而不是只有最近幾條
        recent_messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.created_at.asc()).all()
        for msg in recent_messages:
            conversation_history.append({
                'role': msg.role,
                'content': msg.content
            })
        
        # 生成 LLM 回應 (排除剛添加的用戶訊息)
        llm_result = llm_service.generate_response(user_message, conversation_history[:-1])
        
        # 儲存助手回應
        assistant_msg = Message(
            conversation_id=conversation.id,
            role='assistant',
            content=llm_result['response']
        )
        
        # 設定元數據
        assistant_msg.set_metadata({
            'rag_used': llm_result.get('rag_used', False),
            'sources': llm_result.get('sources', []),
            'processing_steps': llm_result.get('processing_steps', [])
        })
        
        db.session.add(assistant_msg)
        
        # 更新對話時間
        conversation.updated_at = datetime.utcnow()
        
        # 提交到資料庫
        db.session.commit()
        
        # 返回結果
        return jsonify({
            'response': llm_result['response'],
            'session_id': conversation.session_id,
            'conversation_id': conversation.id,
            'message_id': assistant_msg.id,
            'rag_used': llm_result.get('rag_used', False),
            'sources': llm_result.get('sources', [])
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"聊天 API 錯誤: {str(e)}")
        # 在開發模式下返回更詳細的錯誤
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'處理請求時發生錯誤: {str(e)}'}), 500

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """獲取對話列表"""
    try:
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        conversations = Conversation.query.filter_by(is_active=True).order_by(
            Conversation.updated_at.desc()
        ).offset(offset).limit(limit).all()
        
        total = Conversation.query.filter_by(is_active=True).count()
        
        return jsonify({
            'conversations': [conv.to_dict() for conv in conversations],
            'total': total,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"獲取對話列表錯誤: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations/<session_id>', methods=['GET'])
def get_conversation(session_id):
    """獲取特定對話的詳細信息"""
    try:
        conversation = Conversation.query.filter_by(session_id=session_id, is_active=True).first()
        
        if not conversation:
            return jsonify({'error': '對話不存在'}), 404
        
        return jsonify(conversation.to_dict(include_messages=True))
        
    except Exception as e:
        logger.error(f"獲取對話詳情錯誤: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations/<session_id>', methods=['PUT'])
def update_conversation(session_id):
    """更新對話信息"""
    try:
        conversation = Conversation.query.filter_by(session_id=session_id, is_active=True).first()
        
        if not conversation:
            return jsonify({'error': '對話不存在'}), 404
        
        data = request.get_json()
        
        if 'title' in data:
            conversation.title = data['title']
        
        conversation.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'conversation': conversation.to_dict(),
            'message': '對話更新成功'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新對話錯誤: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations/<session_id>', methods=['DELETE'])
def delete_conversation(session_id):
    """刪除對話（軟刪除）"""
    try:
        conversation = Conversation.query.filter_by(session_id=session_id, is_active=True).first()
        
        if not conversation:
            return jsonify({'error': '對話不存在'}), 404
        
        conversation.is_active = False
        conversation.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': '對話刪除成功'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"刪除對話錯誤: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """獲取服務狀態"""
    try:
        llm_status = llm_service.get_service_status()
        
        # 資料庫統計
        total_conversations = Conversation.query.filter_by(is_active=True).count()
        total_messages = Message.query.join(Conversation).filter(Conversation.is_active == True).count()
        
        return jsonify({
            'llm_service': llm_status,
            'database': {
                'total_conversations': total_conversations,
                'total_messages': total_messages
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"獲取狀態錯誤: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search_conversations():
    """搜索對話和訊息"""
    try:
        query_text = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 10))
        
        if not query_text:
            return jsonify({'error': '搜索關鍵詞不能為空'}), 400
        
        # 搜索訊息內容
        messages = Message.query.join(Conversation).filter(
            Conversation.is_active == True,
            Message.content.contains(query_text)
        ).order_by(Message.created_at.desc()).limit(limit).all()
        
        # 組織結果
        results = []
        seen_conversations = set()
        
        for message in messages:
            if message.conversation_id not in seen_conversations:
                conv = message.conversation
                results.append({
                    'conversation': conv.to_dict(),
                    'matched_message': message.to_dict()
                })
                seen_conversations.add(message.conversation_id)
        
        return jsonify({
            'results': results,
            'query': query_text,
            'total': len(results)
        })
        
    except Exception as e:
        logger.error(f"搜索錯誤: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 靜態檔案服務
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """提供前端靜態檔案"""
    frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    
    if path and os.path.exists(os.path.join(frontend_dir, path)):
        return send_from_directory(frontend_dir, path)
    else:
        # 返回主頁面
        index_path = os.path.join(frontend_dir, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(frontend_dir, 'index.html')
        else:
            return "前端檔案不存在", 404

# 初始化資料庫
# 確保資料庫在應用程式上下文內被建立
with app.app_context():
    db.create_all()
    logger.info("資料庫初始化完成")

if __name__ == '__main__':
    logger.info("啟動 LLM 服務...")
    # debug=True 會讓 Flask 在程式碼變更時自動重啟，方便開發
    app.run(host='0.0.0.0', port=5000, debug=True)