from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

class SurveyParser:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=chrome_options)

    def parse_survey(self, url):
        try:
            self.driver.get(url)
            time.sleep(2)  # 等待页面加载
            
            survey_data = {
                "title": self._get_survey_title(),
                "questions": self._get_questions()
            }
            
            return survey_data
            
        except Exception as e:
            print(f"解析问卷时出错: {str(e)}")
            return None
        finally:
            self.driver.quit()
    
    def _get_survey_title(self):
        try:
            title = self.driver.find_element(By.CLASS_NAME, 'htitle').text
            return title
        except:
            return "未命名问卷"
    
    def _get_questions(self):
        questions = []
        # 获取所有问题div
        question_elements = self.driver.find_elements(By.CLASS_NAME, 'field')
        
        for element in question_elements:
            try:
                # 获取问题文本
                question_text = element.find_element(By.CLASS_NAME, 'field-label').text
                
                # 获取问题类型
                question_type = self._get_question_type(element)
                
                # 获取选项
                options = self._get_options(element, question_type)
                
                question = {
                    "id": element.get_attribute("id"),
                    "text": question_text,
                    "type": question_type,
                    "options": options
                }
                questions.append(question)
            except Exception as e:
                print(f"解析问题时出错: {str(e)}")
                continue
                
        return questions
    
    def _get_question_type(self, element):
        # 判断题目类型
        if element.find_elements(By.CLASS_NAME, 'ui-radio'):
            return "单选题"
        elif element.find_elements(By.CLASS_NAME, 'ui-checkbox'):
            return "多选题"
        elif element.find_elements(By.CLASS_NAME, 'ui-input-text'):
            return "填空题"
        elif element.find_elements(By.CLASS_NAME, 'ui-listview'):
            return "排序题"
        elif element.find_elements(By.CLASS_NAME, 'matrix-rating'):
            if element.get_attribute('total'):
                return "比重题"
            else:
                return "矩阵评分题"
        elif element.find_elements(By.CLASS_NAME, 'scale-rating'):
            return "量表题"
        else:
            return "未知类型"
    
    def _get_options(self, element, question_type):
        options = []
        try:
            if question_type == "单选题":
                # 获取单选题选项
                option_elements = element.find_elements(By.CLASS_NAME, 'ui-radio')
                for opt in option_elements:
                    try:
                        # 获取选项文本 - 直接获取父元素的文本内容
                        option_text = opt.text.strip()
                        if option_text:
                            options.append({
                                "text": option_text,
                                "value": opt.get_attribute("value")
                            })
                    except Exception as e:
                        print(f"获取单选题选项时出错: {str(e)}")
                        
            elif question_type == "多选题":
                # 获取多选题选项
                option_elements = element.find_elements(By.CLASS_NAME, 'ui-checkbox')
                for opt in option_elements:
                    try:
                        # 获取选项文本 - 直接获取父元素的文本内容
                        option_text = opt.text.strip()
                        if option_text:
                            options.append({
                                "text": option_text,
                                "value": opt.get_attribute("value")
                            })
                    except Exception as e:
                        print(f"获取多选题选项时出错: {str(e)}")
                        
            elif question_type == "填空题":
                # 填空题不需要选项
                options.append({
                    "text": "填空题",
                    "type": "text"
                })
                
            elif question_type == "排序题":
                # 获取排序题选项
                option_elements = element.find_elements(By.CLASS_NAME, 'ui-li-static')
                for opt in option_elements:
                    try:
                        # 获取选项文本
                        option_text = opt.find_element(By.CSS_SELECTOR, 'div span').text.strip()
                        if option_text:
                            options.append({
                                "text": option_text,
                                "value": opt.find_element(By.CSS_SELECTOR, 'input').get_attribute("value")
                            })
                    except Exception as e:
                        print(f"获取排序题选项时出错: {str(e)}")
                        
            elif question_type == "比重题":
                # 获取比重题选项
                option_elements = element.find_elements(By.CSS_SELECTOR, 'tr[id^="drv"] td.title')
                for opt in option_elements:
                    try:
                        option_text = opt.text.strip()
                        if option_text:
                            options.append({
                                "text": option_text,
                                "type": "weight",
                                "min": 0,
                                "max": int(element.get_attribute('total'))
                            })
                    except Exception as e:
                        print(f"获取比重题选项时出错: {str(e)}")
                        
            elif question_type == "矩阵评分题":
                # 获取矩阵评分题选项
                option_elements = element.find_elements(By.CSS_SELECTOR, 'tr.rowtitle td.title')
                for opt in option_elements:
                    try:
                        option_text = opt.text.strip()
                        if option_text:
                            options.append({
                                "text": option_text,
                                "type": "matrix",
                                "scale": [1, 2, 3, 4, 5]  # 默认5分制
                            })
                    except Exception as e:
                        print(f"获取矩阵评分题选项时出错: {str(e)}")
                        
            elif question_type == "量表题":
                # 获取量表题选项
                scale_elements = element.find_elements(By.CSS_SELECTOR, 'a.rate-off')
                min_val = int(scale_elements[0].get_attribute('val'))
                max_val = int(scale_elements[-1].get_attribute('val'))
                options.append({
                    "text": "量表评分",
                    "type": "scale",
                    "min": min_val,
                    "max": max_val
                })
                
        except Exception as e:
            print(f"获取选项时出错: {str(e)}")
            
        return options 