# C:\llm_service\backend\app.py
# 版本: vFinal 3.6 - 回歸簡潔查詢

import os
import sys
import logging
import json
import uuid
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# --- 設置路徑和載入環境變數 ---
try:
    project_root = Path(__file__).parent.parent
    sys.path.append(str(project_root / "backend"))
    sys.path.append(str(project_root / "rag_system" / "scripts"))
    load_dotenv(project_root / ".env")
except Exception as e:
    print(f"FATAL: Failed to set up paths or load dotenv: {e}")
    sys.exit(1)

# --- 匯入所有需要的服務 ---
from llm_service import LLMService
from multimedia_service import MultimediaService
from weather_service import TaiwanWeatherService

# --- 初始化 Flask 應用和服務 ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{project_root / 'llm_service.db'}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)
db = SQLAlchemy(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("正在初始化所有服務...")
llm_service = LLMService()
multimedia_service = MultimediaService()
weather_service = TaiwanWeatherService()
logger.info("所有服務初始化完成。")

# --- 資料庫模型 ---
class Conversation(db.Model):
    __tablename__='conversations';id=db.Column(db.Integer,primary_key=True);session_id=db.Column(db.String(255),unique=True,nullable=False,default=lambda:str(uuid.uuid4()));title=db.Column(db.String(500),nullable=True);created_at=db.Column(db.DateTime,default=datetime.utcnow);updated_at=db.Column(db.DateTime,default=datetime.utcnow,onupdate=datetime.utcnow);is_active=db.Column(db.Boolean,default=True);messages=db.relationship('Message',backref='conversation',lazy=True,cascade='all, delete-orphan')
    def to_dict(self,include_messages=False):
        result={'id':self.id,'session_id':self.session_id,'title':self.title or self.get_auto_title(),'created_at':self.created_at.isoformat()if self.created_at else None,'updated_at':self.updated_at.isoformat()if self.updated_at else None,'is_active':self.is_active,'message_count':len(self.messages)};
        if include_messages:result['messages']=[msg.to_dict()for msg in self.messages];
        return result
    def get_auto_title(self):
        if self.title:return self.title
        first_user_message=next((msg for msg in self.messages if msg.role=='user'),None);
        if first_user_message:content=first_user_message.content[:30];return content+"..."if len(first_user_message.content)>30 else content
        return f"對話 {self.created_at.strftime('%m-%d %H:%M')}"

class Message(db.Model):
    __tablename__='messages';id=db.Column(db.Integer,primary_key=True);conversation_id=db.Column(db.Integer,db.ForeignKey('conversations.id'),nullable=False);role=db.Column(db.String(50),nullable=False);content=db.Column(db.Text,nullable=False);message_metadata=db.Column(db.Text,nullable=True);created_at=db.Column(db.DateTime,default=datetime.utcnow)
    def to_dict(self):return{'id':self.id,'conversation_id':self.conversation_id,'role':self.role,'content':self.content,'metadata':json.loads(self.message_metadata)if self.message_metadata else{},'created_at':self.created_at.isoformat()if self.created_at else None}
    def set_metadata(self,metadata_dict):self.message_metadata=json.dumps(metadata_dict,ensure_ascii=False)

# [核心修正] 簡化城市提取，不再轉換為 "臺"
def _extract_city_from_message(message):
    if not weather_service: return None
    # 使用簡稱列表進行匹配，並按長度排序以提高準確性
    taiwan_cities = [
        '台北', '新北', '桃園', '台中', '台南', '高雄',
        '基隆', '新竹', '嘉義', '宜蘭', '花蓮', '台東', '苗栗', '彰化',
        '南投', '雲林', '屏東', '澎湖', '金門', '連江'
    ]
    for city in sorted(taiwan_cities, key=len, reverse=True):
        if city in message:
            return city # 直接返回找到的簡稱，例如 "台北"
    return None

# --- 核心聊天 API ---
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data: return jsonify({'error': '無效的 JSON 資料'}), 400
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')
        conversation_history = data.get('conversation_history', [])
        if not user_message: return jsonify({'error': '訊息不能為空'}), 400
        
        conversation = None
        if session_id: conversation = Conversation.query.filter_by(session_id=session_id, is_active=True).first()
        if not conversation: conversation = Conversation(); db.session.add(conversation); db.session.flush()
        
        user_msg = Message(conversation_id=conversation.id, role='user', content=user_message); db.session.add(user_msg)
        
        # 智慧判斷
        weather_keywords = ['天氣', '氣溫', '下雨', '預報', '颱風', '濕度', '氣壓']; is_weather_question = any(keyword in user_message for keyword in weather_keywords)
        use_rag_static = True; use_rag_dynamic = False; query_for_rag = user_message

        if is_weather_question:
            use_rag_dynamic = True
            if len(user_message) < 20: use_rag_static = False
        
        logger.info(f"查詢意圖: 靜態庫-{'啟用' if use_rag_static else '停用'}, 動態庫-{'啟用' if use_rag_dynamic else '停用'}")
        
        llm_result = llm_service.generate_response(
            user_query=query_for_rag, 
            conversation_history=conversation_history,
            use_rag_static=use_rag_static,
            use_rag_dynamic=use_rag_dynamic
        )
        
        assistant_msg = Message(conversation_id=conversation.id, role='assistant', content=llm_result['response']); assistant_msg.set_metadata(llm_result); db.session.add(assistant_msg)
        db.session.commit()
        
        llm_result['session_id'] = conversation.session_id
        return jsonify(llm_result)
        
    except Exception as e:
        db.session.rollback(); logger.error(f"聊天 API 錯誤: {e}", exc_info=True)
        return jsonify({'error': f'處理請求時發生錯誤: {e}'}), 500

# --- 所有其他 API 端點 ---
@app.route('/api/status')
def get_status(): return jsonify({'success': True, 'message': 'LLM Backend Service is running.'})
@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    try:
        conversations = Conversation.query.filter_by(is_active=True).order_by(Conversation.updated_at.desc()).all()
        return jsonify({'conversations': [conv.to_dict() for conv in conversations], 'total': len(conversations)})
    except Exception as e: return jsonify({'error': str(e)}), 500

# --- 啟動與初始化 ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)