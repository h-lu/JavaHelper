import os
from typing import List, Dict
from doc_parser import GuideParser

class LectureManager:
    def __init__(self, lecture_dir: str = "lecture"):
        self.lecture_dir = lecture_dir
        self.ensure_lecture_dir()
        
    def ensure_lecture_dir(self):
        """确保教案目录存在"""
        if not os.path.exists(self.lecture_dir):
            os.makedirs(self.lecture_dir)
            
    def get_available_lectures(self) -> List[Dict[str, str]]:
        """获取所有可用的教案"""
        lectures = []
        for filename in os.listdir(self.lecture_dir):
            if filename.endswith(('.qmd', '.md')):
                name = os.path.splitext(filename)[0]
                lectures.append({
                    "name": name,
                    "path": os.path.join(self.lecture_dir, filename)
                })
        return lectures
    
    def load_lecture(self, lecture_path: str) -> GuideParser:
        """加载指定的教案"""
        return GuideParser(lecture_path) 