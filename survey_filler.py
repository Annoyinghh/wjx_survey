from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    TimeoutException, 
    ElementClickInterceptedException, 
    ElementNotInteractableException,
    StaleElementReferenceException,
    InvalidElementStateException,
)
from ai_answer import AIAnswerGenerator
import time
import random
import json
import os
from datetime import datetime

class SurveyFiller:
    def __init__(self):
        chrome_options = Options()
        # --- 基础设置 ---
        # 默认使用无头模式在后台运行，如需调试可暂时注释掉下一行
        chrome_options.add_argument('--headless') 
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # --- 反爬虫关键设置 (参考自你提供的资料) ---
        # 1. 禁用 "Chrome正在受到自动软件的控制" 提示
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        # 2. 禁用自动化扩展
        chrome_options.add_experimental_option('useAutomationExtension', False)
        # 3. 设置伪造的 User-Agent (建议添加，防止因无头模式默认UA被识破)
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # 性能优化配置 (保留你原有的)
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-field-trial-config')
        chrome_options.add_argument('--disable-ipc-flooding-protection')

        self.driver = webdriver.Chrome(options=chrome_options)
        
        # --- CDP 命令注入 (核心反爬逻辑) ---
        # 在页面加载前执行 JS，将 navigator.webdriver 设置为 undefined
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        })
        
        self.ai_generator = AIAnswerGenerator()
        self.ai_call_count = {}
        self.use_ai = False
        self.weights = {}
        self.failure_count = 0
        
    def _save_failure_screenshot(self, error_type, details=""):
        """保存失败截图"""
        try:
            # 创建失败截图目录
            failure_dir = "failure_screenshots"
            if not os.path.exists(failure_dir):
                os.makedirs(failure_dir)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{failure_dir}/failure_{error_type}_{timestamp}.png"
            
            # 保存截图
            self.driver.save_screenshot(filename)
            
            # 保存错误详情到文本文件
            error_file = filename.replace('.png', '.txt')
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(f"错误类型: {error_type}\n")
                f.write(f"错误详情: {details}\n")
                f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"当前URL: {self.driver.current_url}\n")
                f.write(f"页面标题: {self.driver.title}\n")
            
            print(f"失败截图已保存: {filename}")
            return filename
        except Exception as e:
            print(f"保存失败截图时出错: {e}")
            return None
        
    def _reset_ai_call_count(self, question_id):
        """重置指定题目的AI调用次数"""
        self.ai_call_count[question_id] = 0
        
    def _can_call_ai(self, question_id):
        """检查是否可以调用AI"""
        if question_id not in self.ai_call_count:
            self._reset_ai_call_count(question_id)
        return self.ai_call_count[question_id] < 5
        
    def _increment_ai_call_count(self, question_id):
        """增加AI调用次数"""
        if question_id not in self.ai_call_count:
            self._reset_ai_call_count(question_id)
        self.ai_call_count[question_id] += 1
        
    def _click_option(self, option, is_multi=False, fill_other_text=None):
        """点击单个选项（精简日志与等待，避免无效阻塞）"""
        try:
            # 尝试获取选项标签文本（仅用于 AI 提示词）
            label_text = ''
            try:
                label_element = option.find_element(By.XPATH, '..//..//div[@class="label"]')
                label_text = label_element.text
            except:
                try:
                    label_element = option.find_element(By.XPATH, '..//..//label')
                    label_text = label_element.text
                except:
                    try:
                        parent = option.find_element(By.XPATH, '..')
                        label_text = parent.text
                    except:
                        label_text = "未知选项"
            
            # 直接点击 a 标签，不依赖 span 包装器
            self.driver.execute_script("arguments[0].scrollIntoView(true);", option)
            time.sleep(0.1)
            self.driver.execute_script("arguments[0].click();", option)
            time.sleep(0.2)
            
            # 检查是否需要填写“其他”文本框
            try:
                input_box = WebDriverWait(option, 1.5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.ui-text input'))
                )

                # 如果输入框不可见或不可交互，直接返回，不再强行 send_keys，避免 element not interactable
                if not input_box.is_displayed() or not input_box.is_enabled():
                    return True

                self.driver.execute_script("arguments[0].scrollIntoView(true);", input_box)
                input_box.click()
                self.driver.execute_script("arguments[0].value = '';", input_box)
                
                if self.use_ai:
                    # 获取问题ID
                    question_div = option.find_element(By.XPATH, 'ancestor::div[contains(@class, "field")]')
                    question_id = question_div.get_attribute('id')
                    
                    # 检查是否可以调用AI
                    if not self._can_call_ai(question_id):
                        print(f"题目 {question_id} 已达到AI调用次数限制(5次)")
                        return True
                    
                    # 获取问题文本和已选择的选项
                    question_text = question_div.find_element(By.CLASS_NAME, 'field-label').text
                    
                    selected_options = []
                    if is_multi:
                        selected_checkboxes = question_div.find_elements(
                            By.CSS_SELECTOR,
                            'div.ui-checkbox input[type="checkbox"]:checked'
                        )
                        for checkbox in selected_checkboxes:
                            try:
                                option_label = checkbox.find_element(
                                    By.XPATH,
                                    '..//..//div[@class="label"]'
                                ).text
                                selected_options.append(option_label)
                            except:
                                continue
                    
                    prompt = f"问题：{question_text}\n"
                    if selected_options:
                        prompt += f"已选择的选项：{', '.join(selected_options)}\n"
                    prompt += f"当前选项：{label_text}\n"
                    prompt += "请根据以上信息，生成一个合理的补充说明。"
                    
                    answer = self.ai_generator.generate_answer(prompt)
                    # 增加AI调用次数
                    self._increment_ai_call_count(question_id)
                else:
                    answer = "无"
                
                input_box.send_keys(answer)
            except TimeoutException:
                # 没有找到输入框，说明不需要填空
                pass
            except Exception as e:
                # 避免因为“其他”输入框不可用而卡整题，直接略过
                print(f'填写答案失败: {e}')
            
            return True
        except Exception as e:
            print(f"点击选项失败: {e}")
            return False
            
    def _wait_and_click(self, element, max_retries=3):
        """等待并点击元素，带重试机制"""
        for i in range(max_retries):
            try:
                # 等待元素可交互
                WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(element)
                )
                # 确保元素在视图中
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.5)
                # 尝试点击
                element.click()
                return True
            except (ElementClickInterceptedException, ElementNotInteractableException):
                self._remove_shade()
                time.sleep(1)
                try:
                    self.driver.execute_script("arguments[0].click();", element)
                    return True
                except:
                    pass
            except (StaleElementReferenceException, InvalidElementStateException):
                time.sleep(1)
                continue
        return False
            
    def _wait_for_submit_success(self):
        """等待提交成功"""
        try:
            # 等待提交成功提示出现
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "layui-layer-content"))
            )
            # 检查是否包含成功信息
            success_text = self.driver.find_element(By.CLASS_NAME, "layui-layer-content").text
            return "提交成功" in success_text
        except:
            return False
            
    def fill_survey(self, url, weights=None):
        try:
            print(f"开始填写问卷: {url}")
            print(f"权重设置: {json.dumps(weights, ensure_ascii=False, indent=2)}")
            
            self.driver.get(url)
            time.sleep(3)  # 等待页面完全加载
            
            # 尝试多种选择器来查找问题
            questions = []
            selectors = [
                (By.CLASS_NAME, 'field'),
                (By.CSS_SELECTOR, '[class*="question"]'),
                (By.CSS_SELECTOR, '[class*="Question"]'),
                (By.CSS_SELECTOR, '.field-label'),
                (By.CSS_SELECTOR, '[class*="item"]'),
                (By.CSS_SELECTOR, '[class*="Item"]')
            ]
            
            for selector in selectors:
                try:
                    questions = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_all_elements_located(selector)
                    )
                    if questions:
                        print(f"使用选择器 {selector} 找到 {len(questions)} 个问题")
                        break
                except:
                    continue
            
            if not questions:
                print("未找到问题，尝试查找所有输入元素")
                # 如果找不到问题容器，直接查找所有输入元素
                all_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input, textarea, select")
                print(f"找到 {len(all_inputs)} 个输入元素")
                if not all_inputs:
                    self._save_failure_screenshot("no_questions_found", "页面加载后未找到任何问题或输入元素")
                    return False
                return self._fill_all_inputs(all_inputs)
            
            print(f"找到{len(questions)}个问题")
            
            # 处理多页问卷的主循环
            page_count = 1
            max_pages = 10  # 防止无限循环
            
            while page_count <= max_pages:
                print(f"\n========== 处理第 {page_count} 页 ==========")
                
                # 获取当前页的所有问题
                try:
                    questions = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_all_elements_located((By.CLASS_NAME, 'field'))
                    )
                    print(f"第 {page_count} 页找到 {len(questions)} 个问题")
                except Exception as e:
                    print(f"加载第 {page_count} 页问题失败: {e}")
                    break
                
                # 填写当前页的所有问题
                for idx, question in enumerate(questions, 1):
                    try:
                        # 对带有逻辑跳转的问卷（如问卷星），未命中的分支题通常是隐藏的
                        # 如果当前题目在页面上不可见，说明不在本次答题分支中，直接跳过
                        if not question.is_displayed():
                            print(f"第{idx}题当前不可见，推测为其他分支题，跳过")
                            continue

                        question_text = question.find_element(By.CLASS_NAME, 'field-label').text
                        question_type = self._get_question_type(question)
                        question_id = question.get_attribute('id')
                        
                        print(f"处理第{idx}题: {question_text}")
                        print(f"题目类型: {question_type}")
                        
                        if question_type == "填空题":
                            self._fill_blank(idx)
                        elif question_type == "多选题":
                            self._handle_multi_choice(idx, self.weights)
                        elif question_type == "单选题":
                            self._handle_single_choice(idx, self.weights)
                        elif question_type == "排序题":
                            self._handle_sort_question(idx)
                        elif question_type == "比重题":
                            self._handle_weight_question(idx)
                        elif question_type == "矩阵评分题":
                            self._handle_matrix_question(idx)
                        elif question_type == "量表题":
                            self._handle_scale_question(idx)
                        
                        time.sleep(1)  # 问题间等待时间
                    except Exception as e:
                        print(f"处理第{idx}题时出错: {str(e)}")
                        self._save_failure_screenshot(f"question_{idx}_error", f"处理第{idx}题时出错: {str(e)}")
                        continue
                
                # 当前页填写完成，检查是否有下一页
                print(f"\n第 {page_count} 页填写完成，检查是否有下一页...")
                next_button = self._find_next_button()
                
                if next_button:
                    # 存在下一页，点击下一页按钮
                    print(f"检测到下一页按钮，准备点击...")
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                        time.sleep(0.5)
                        next_button.click()
                        print(f"已点击下一页按钮")
                        time.sleep(3)  # 等待页面加载
                        
                        # 等待新的问题加载（而不是检查URL，因为问卷星使用#路由）
                        try:
                            WebDriverWait(self.driver, 5).until(
                                EC.presence_of_all_elements_located((By.CLASS_NAME, 'field'))
                            )
                            print(f"下一页已加载")
                        except TimeoutException:
                            print(f"等待下一页加载超时")
                            break
                        
                        page_count += 1
                        
                        # 继续循环处理下一页
                        continue
                    except Exception as e:
                        print(f"点击下一页按钮失败: {e}")
                        break
                else:
                    # 不存在下一页，说明已到最后一页，执行提交
                    print(f"未检测到下一页按钮，说明已到最后一页，准备提交问卷...")
                    submit_result = self._find_and_submit()
                    if not submit_result:
                        self._save_failure_screenshot("submit_failed", "提交按钮点击失败或提交后未成功")
                    return submit_result
            
            print(f"超过最大页数限制 ({max_pages})，停止处理")
            return False
        except Exception as e:
            print(f"填写问卷时出错: {str(e)}")
            self._save_failure_screenshot("general_error", f"填写问卷时发生一般错误: {str(e)}")
            return False
        
    def _get_question_type(self, element):
        # 判断题目类型
        if element.find_elements(By.CLASS_NAME, 'ui-radio'):
            return "单选题"
        elif element.find_elements(By.CLASS_NAME, 'ui-checkbox'):
            return "多选题"
        elif element.find_elements(By.CLASS_NAME, 'ui-input-text'):
            return "填空题"
        elif element.find_elements(By.TAG_NAME, 'textarea'):
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
        
    def _find_next_button(self):
        """查找下一页按钮 - 更精确的识别"""
        try:
            # 问卷星的下一页按钮通常有以下几种选择器
            # 按优先级排序，最精确的放在前面
            selectors = [
                # 最精确的选择器
                (By.ID, 'ctlNext'),  # 问卷星常用ID
                (By.XPATH, '//a[@id="ctlNext" and contains(text(), "下一页")]'),
                (By.XPATH, '//input[@id="ctlNext" and @value="下一页"]'),
                
                # 其次是精确的文本匹配
                (By.XPATH, '//a[text()="下一页"]'),
                (By.XPATH, '//button[text()="下一页"]'),
                (By.XPATH, '//input[@type="button" and @value="下一页"]'),
                (By.XPATH, '//input[@type="submit" and @value="下一页"]'),
                
                # 最后才是模糊匹配
                (By.XPATH, '//a[contains(text(), "下一页")]'),
                (By.XPATH, '//button[contains(text(), "下一页")]'),
            ]
            
            for selector in selectors:
                try:
                    buttons = self.driver.find_elements(*selector)
                    for button in buttons:
                        # 检查按钮是否真的可见和可用
                        if button.is_displayed() and button.is_enabled():
                            # 额外检查：确保不是"提交"或"完成"按钮
                            button_text = button.text.strip()
                            button_value = button.get_attribute('value') or ''
                            
                            if '下一页' in button_text or '下一页' in button_value:
                                print(f"找到下一页按钮: {selector}, 文本: {button_text}")
                                return button
                except:
                    continue
            
            print("未找到下一页按钮")
            return None
        except Exception as e:
            print(f"查找下一页按钮时出错: {e}")
            return None
    
    def close(self):
        self.driver.quit()
        
    def _fill_all_inputs(self, inputs):
        """直接填写所有输入元素"""
        try:
            print("开始直接填写所有输入元素")
            
            # 查找所有选项
            options = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio'], input[type='checkbox']")
            print(f"找到 {len(options)} 个选项")
            
            # 随机选择一些选项
            if options:
                num_to_select = min(random.randint(3, 8), len(options))
                selected_options = random.sample(options, num_to_select)
                
                for i, option in enumerate(selected_options):
                    try:
                        print(f"点击选项 {i+1}")
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", option)
                        time.sleep(0.2)  # 滚动等待时间
                        self.driver.execute_script("arguments[0].click();", option)
                        time.sleep(0.5)  # 点击后等待时间
                    except Exception as e:
                        print(f"点击选项 {i+1} 失败: {e}")
            
            # 查找所有文本输入
            text_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea")
            print(f"找到 {len(text_inputs)} 个文本输入")
            
            # 填写文本输入
            for i, text_input in enumerate(text_inputs):
                try:
                    print(f"填写文本输入 {i+1}")
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", text_input)
                    time.sleep(0.2)  # 滚动等待时间
                    text_input.clear()
                    text_input.send_keys("测试答案")
                    time.sleep(0.5)  # 填写后等待时间
                except Exception as e:
                    print(f"填写文本输入 {i+1} 失败: {e}")
            
            # 查找并点击提交按钮
            return self._find_and_submit()
            
        except Exception as e:
            print(f"填写输入元素时出错: {e}")
            return False
            
    def _is_option_selected(self, option):
        """检查选项是否被选中"""
        try:
            # 检查input的checked属性
            if option.tag_name == 'input':
                return option.is_selected()
            
            # 检查父元素中是否有选中的input
            parent = option.find_element(By.XPATH, '..')
            input_element = parent.find_element(By.CSS_SELECTOR, 'input[type="checkbox"]')
            return input_element.is_selected()
        except:
            return False
            
    def _find_and_submit(self):
        """查找并点击提交按钮，并处理智能验证"""
        try:
            print("开始查找提交按钮")
            
            # ... (保留你原有的查找 submit_button 的代码逻辑) ...
            # 假设这里已经找到了 submit_button (为了篇幅省略查找过程)
            # 建议使用 ID 查找，问卷星通常是 ctlNext 或 submit_button
            try:
                submit_button = self.driver.find_element(By.ID, "ctlNext")
            except:
                # 回退到你原有的查找逻辑
                submit_button = self.driver.find_element(By.CSS_SELECTOR, ".submit-btn, #ctlNext")

            if submit_button:
                print("准备提交问卷")
                self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                time.sleep(1)
                # 点击提交
                submit_button.click()
                print("点击提交按钮...")
                
                # --- 新增：处理智能验证逻辑 ---
                time.sleep(1) # 等待一下看是否有弹窗
                
                # 检测是否出现智能验证按钮 (通常是一个弹窗里的按钮)
                try:
                    # 等待验证按钮出现（问卷星常见的验证按钮ID是 SM_BTN_1 或样式）
                    verify_btn = WebDriverWait(self.driver, 3).until(
                        EC.visibility_of_element_located((By.XPATH, "//*[@id='SM_BTN_1'] | //div[contains(@class,'rect-btn')]"))
                    )
                    print("检测到智能验证，尝试自动点击...")
                    verify_btn.click()
                    time.sleep(3) # 等待验证通过
                except TimeoutException:
                    print("未检测到简单的点击验证，检查是否是滑块或无需验证")
                except Exception as e:
                    print(f"验证处理出错: {e}")

                # 检测是否出现滑块验证 (更复杂，这里提供基础思路)
                try:
                    slider = self.driver.find_element(By.XPATH, "//span[@id='nc_1_n1z']")
                    print("检测到滑块验证，尝试滑动...")
                    action = ActionChains(self.driver)
                    action.click_and_hold(slider).perform()
                    action.move_by_offset(300, 0).perform() # 拖动距离
                    action.release().perform()
                    time.sleep(2)
                except:
                    pass

                # --- 验证结束，检查结果 ---
                
                # 等待提交结果
                time.sleep(2)
                current_url = self.driver.current_url
                page_source = self.driver.page_source
                
                if "success" in current_url.lower() or "thank" in current_url.lower() or "感谢" in page_source:
                    print("问卷提交成功")
                    return True
                else:
                    print("问卷提交可能失败或需要进一步验证")
                    self._save_failure_screenshot("submit_check", "提交后未跳转成功页面")
                    return False
            else:
                print("未找到提交按钮")
                return False
                
        except Exception as e:
            print(f"提交问卷时出错: {e}")
            return False

    def _fill_blank(self, question_index):
        # 先找input[type="text"]，找不到再找textarea
        xpath_input = f'//div[@id="div{question_index}"]//input[@type="text"]'
        xpath_textarea = f'//div[@id="div{question_index}"]//textarea'
        input_field = None
        try:
            input_field = self.driver.find_element(By.XPATH, xpath_input)
        except:
            try:
                input_field = self.driver.find_element(By.XPATH, xpath_textarea)
            except Exception as e:
                print(f"填空题第{question_index}题XPath填写失败: {e}")
                self._save_failure_screenshot(f"fill_blank_{question_index}_error", f"填空题第{question_index}题XPath填写失败: {e}")
                return

        print('--- 填空input/textarea outerHTML ---')
        print(input_field.get_attribute('outerHTML'))

        self.driver.execute_script("arguments[0].scrollIntoView(true);", input_field)
        time.sleep(0.2)
        input_field.click()  # 激活输入框
        self.driver.execute_script("arguments[0].value = '';", input_field)
        time.sleep(0.1)

        if self.use_ai:
            # 获取问题文本
            try:
                question_text = self.driver.find_element(By.XPATH, f'//div[@id=\"div{question_index}\"]//div[@class=\"field-label\"]').text
            except:
                question_text = ""
            print(f"填空题问题: {question_text}")

            # 使用AI生成回答
            answer = self.ai_generator.generate_answer(question_text)
            print(f"AI生成的回答: {answer}")
        else:
            answer = "无"
            print("不使用AI，填写默认答案：无")

        input_field.send_keys(answer)
        print(f"填空题第{question_index}题已填写: {answer}")

    def _handle_sort_question(self, question_index):
        """处理排序题"""
        try:
            # 获取所有选项
            options = self.driver.find_elements(By.XPATH, f'//div[@id="div{question_index}"]//li[@class="ui-li-static"]')
            # 随机打乱选项顺序
            random_order = list(range(1, len(options) + 1))
            random.shuffle(random_order)
            
            # 点击选项进行排序
            for i, option in enumerate(options):
                self.driver.execute_script("arguments[0].scrollIntoView(true);", option)
                option.click()
                time.sleep(random.uniform(0.2, 0.5))
            print(f"排序题第{question_index}题已完成排序")
        except Exception as e:
            print(f"排序题处理失败: {e}")
            
    def _handle_weight_question(self, question_index):
        """处理比重题"""
        try:
            # 只选取可见且可用的输入框
            inputs = [
                el for el in self.driver.find_elements(
                    By.XPATH, f'//div[@id="div{question_index}"]//input[@type="text" and not(@disabled)]'
                ) if el.is_displayed()
            ]
            n = len(inputs)
            total = 100

            # 获取最重要选项的下标
            question_id = f"div{question_index}"
            max_index = self.weights.get(question_id, 0)  # 默认第一个选项最重要
            print(f"比重题第{question_index}题，最重要选项下标: {max_index}")
            
            # 计算权重：最重要的选项占55-65%，其他选项随机分配剩余权重
            max_weight = random.randint(55, 65)  # 最重要选项的权重范围
            remaining_weight = total - max_weight
            
            # 为其他选项生成随机权重
            other_weights = []
            remaining_options = n - 1
            
            if remaining_options > 1:
                # 生成随机权重，确保每个选项至少15%
                min_weight = 15
                max_possible = remaining_weight - (min_weight * (remaining_options - 1))
                
                # 生成第一个随机权重
                first_weight = random.randint(min_weight, min(max_possible, 25))
                other_weights.append(first_weight)
                
                # 生成其他随机权重
                for i in range(remaining_options - 2):
                    current_max = remaining_weight - sum(other_weights) - (min_weight * (remaining_options - len(other_weights) - 1))
                    weight = random.randint(min_weight, min(current_max, 25))
                    other_weights.append(weight)
                
                # 最后一个权重用剩余值
                other_weights.append(remaining_weight - sum(other_weights))
            else:
                # 如果只有一个其他选项，直接分配剩余权重
                other_weights = [remaining_weight]
            
            # 构建最终权重列表
            weights = [0] * n
            weights[max_index] = max_weight
            other_index = 0
            for i in range(n):
                if i != max_index:
                    weights[i] = other_weights[other_index]
                    other_index += 1
            
            print(f"比重题第{question_index}题的权重分配: {weights}")
            print(f"权重总和: {sum(weights)}")

            # 填写权重并触发事件
            for i, (input_field, weight) in enumerate(zip(inputs, weights)):
                self.driver.execute_script("arguments[0].scrollIntoView(true);", input_field)
                input_field.click()
                input_field.clear()
                # 使用JavaScript直接设置值，避免触发多次事件
                self.driver.execute_script(f"arguments[0].value = '{weight}';", input_field)
                # 只在最后一个输入框触发一次事件
                if i == len(inputs) - 1:
                    self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", input_field)
                    self.driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", input_field)
                time.sleep(random.uniform(0.2, 0.5))
            print(f"比重题第{question_index}题已完成填写，总和：{sum(weights)}，分配：{weights}")
        except Exception as e:
            print(f"比重题处理失败: {e}")
            print(f"错误详情: {str(e)}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")
            
    def _handle_matrix_question(self, question_index):
        """处理矩阵评分题"""
        try:
            # 获取所有评分行
            rows = self.driver.find_elements(By.XPATH, f'//div[@id="div{question_index}"]//tr[@tp="d"]')
            
            # 先滚动到问题区域
            question_div = self.driver.find_element(By.ID, f'div{question_index}')
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", question_div)
            time.sleep(0.5)  # 等待滚动完成
            
            # 获取权重设置
            weights = self.weights.get(f"div{question_index}", {"negative": 0.3, "positive": 0.7})
            negative_weight = weights.get("negative", 0.3)
            positive_weight = weights.get("positive", 0.7)
            
            print(f"矩阵题权重设置: 负向={negative_weight}, 正向={positive_weight}")
            
            for row in rows:
                try:
                    # 获取该行的所有评分选项
                    options = row.find_elements(By.CSS_SELECTOR, 'a.rate-off')
                    if not options:
                        continue
                    
                    # 根据权重选择正向或负向评分
                    mid_point = len(options) // 2
                    if random.random() < negative_weight:  # 修改这里，使用negative_weight
                        # 负向评分（选择前半部分）
                        valid_options = options[:mid_point]
                    else:
                        # 正向评分（选择后半部分）
                        valid_options = options[mid_point:]
                    
                    if valid_options:
                        option = random.choice(valid_options)
                        print(f"选择评分: {option.get_attribute('dval')}")
                        
                        # 确保元素在视图中且可点击
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", option)
                        time.sleep(0.3)  # 等待滚动完成
                        
                        # 尝试点击，如果失败则使用JavaScript点击
                        try:
                            option.click()
                        except:
                            self.driver.execute_script("arguments[0].click();", option)
                        
                        time.sleep(random.uniform(0.2, 0.5))
                except Exception as e:
                    print(f"处理矩阵评分行时出错: {e}")
                    continue
                    
            print(f"矩阵评分题第{question_index}题已完成评分")
        except Exception as e:
            print(f"矩阵评分题处理失败: {e}")
            
    def _handle_scale_question(self, question_index):
        """处理量表题"""
        try:
            # 获取所有评分选项
            options = self.driver.find_elements(By.XPATH, f'//div[@id="div{question_index}"]//a[contains(@class, "rate-off")]')
            
            # 获取权重设置
            weights = self.weights.get(f"div{question_index}", {"negative": 0.3, "positive": 0.7})
            negative_weight = weights.get("negative", 0.3)
            positive_weight = weights.get("positive", 0.7)
            
            print(f"量表题权重设置: 负向={negative_weight}, 正向={positive_weight}")
            
            # 根据权重选择正向或负向评分
            mid_point = len(options) // 2
            if random.random() < negative_weight:  # 修改这里，使用negative_weight
                # 负向评分（选择前半部分）
                valid_options = options[:mid_point]
            else:
                # 正向评分（选择后半部分）
                valid_options = options[mid_point:]
            
            if valid_options:
                option = random.choice(valid_options)
                print(f"选择评分: {option.get_attribute('dval')}")
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", option)
                time.sleep(0.3)
                try:
                    option.click()
                except:
                    self.driver.execute_script("arguments[0].click();", option)
                time.sleep(random.uniform(0.2, 0.5))
            print(f"量表题第{question_index}题已完成评分")
        except Exception as e:
            print(f"量表题处理失败: {e}") 

    def _handle_single_choice(self, question_index, weights=None):
        """处理单选题"""
        try:
            # 获取权重设置
            question_id = f"div{question_index}"
            option_weights = weights.get(question_id, {}) if weights else {}
            
            print(f"单选题第{question_index}题权重设置: {option_weights}")
            
            # 获取所有选项
            options = self.driver.find_elements(By.XPATH, f'//div[@id="div{question_index}"]//a[contains(@class, "jqradio")]')
            
            if not options:
                print(f"单选题第{question_index}题未找到选项")
                return False
            
            # 根据权重选择选项
            if option_weights:
                # 过滤掉权重为0的选项
                valid_options = []
                valid_weights = []
                
                for i, option in enumerate(options):
                    # 前端传递的是字符串索引，需要转换为字符串
                    weight = option_weights.get(str(i), 1)  # 默认权重为1
                    print(f"选项{i}权重: {weight}")
                    if weight > 0:
                        valid_options.append(option)
                        valid_weights.append(weight)
                
                if valid_options:
                    # 根据权重随机选择
                    total_weight = sum(valid_weights)
                    if total_weight > 0:
                        rand_val = random.uniform(0, total_weight)
                        cumulative_weight = 0
                        selected_option = None
                        
                        for option, weight in zip(valid_options, valid_weights):
                            cumulative_weight += weight
                            if rand_val <= cumulative_weight:
                                selected_option = option
                                break
                        
                        if selected_option:
                            # 检查是否是"其他"选项
                            is_other_option = self._is_other_option(selected_option)
                            
                            self._click_option(selected_option)
                            print(f"单选题第{question_index}题根据权重选择了选项")
                            
                            # 如果是"其他"选项，需要填写补充内容
                            if is_other_option:
                                question_element = self.driver.find_element(By.XPATH, f'//div[@id="div{question_index}"]')
                                self._fill_other_option_text(question_element)
                            
                            return True
            
            # 如果没有权重设置或权重都为0，随机选择
            option = random.choice(options)
            
            # 检查是否是"其他"选项
            is_other_option = self._is_other_option(option)
            
            self._click_option(option)
            print(f"单选题第{question_index}题随机选择了选项")
            
            # 如果是"其他"选项，需要填写补充内容
            if is_other_option:
                question_element = self.driver.find_element(By.XPATH, f'//div[@id="div{question_index}"]')
                self._fill_other_option_text(question_element)
            
            return True
            
        except Exception as e:
            print(f"单选题第{question_index}题处理失败: {e}")
            self._save_failure_screenshot(f"single_choice_{question_index}_error", f"单选题第{question_index}题处理失败: {e}")
            return False 

    def _handle_multi_choice(self, question_index, weights=None):
        """处理多选题"""
        try:
            # 获取权重设置
            question_id = f"div{question_index}"
            option_weights = weights.get(question_id, {}) if weights else {}
            
            print(f"多选题第{question_index}题权重设置: {option_weights}")
            
            # 获取所有选项 - 尝试多种选择器
            options = []
            selectors = [
                f'//div[@id="div{question_index}"]//a[contains(@class, "jqcheckbox")]',
                f'//div[@id="div{question_index}"]//a[contains(@class, "checkbox")]',
                f'//div[@id="div{question_index}"]//span[contains(@class, "checkbox")]',
                f'//div[@id="div{question_index}"]//div[contains(@class, "checkbox")]',
                f'//div[@id="div{question_index}"]//*[contains(@class, "checkbox")]',
                # 最后尝试隐藏的input，但需要点击其可见的UI元素
                f'//div[@id="div{question_index}"]//input[@type="checkbox"]'
            ]
            
            for selector in selectors:
                try:
                    options = self.driver.find_elements(By.XPATH, selector)
                    if options:
                        print(f"多选题第{question_index}题使用选择器 '{selector}' 找到 {len(options)} 个选项")
                        break
                except Exception as e:
                    print(f"选择器 '{selector}' 查找失败: {e}")
                    continue
            
            if not options:
                print(f"多选题第{question_index}题未找到选项")
                return False
            
            # 根据权重选择选项
            selected_count = 0
            max_selections = min(len(options), 3)  # 最多选择3个选项
            
            if option_weights:
                # 过滤掉权重为0的选项
                valid_options = []
                valid_weights = []
                
                for i, option in enumerate(options):
                    # 前端传递的是字符串索引，需要转换为字符串
                    weight = option_weights.get(str(i), 1)  # 默认权重为1
                    print(f"选项{i}权重: {weight}")
                    if weight > 0:
                        valid_options.append(option)
                        valid_weights.append(weight)
                
                if valid_options:
                    # 根据权重随机选择多个选项
                    for _ in range(max_selections):
                        if not valid_options or selected_count >= max_selections:
                            break
                        
                        total_weight = sum(valid_weights)
                        if total_weight > 0:
                            rand_val = random.uniform(0, total_weight)
                            cumulative_weight = 0
                            selected_index = None
                            
                            for i, weight in enumerate(valid_weights):
                                cumulative_weight += weight
                                if rand_val <= cumulative_weight:
                                    selected_index = i
                                    break
                            
                            if selected_index is not None:
                                selected_option = valid_options[selected_index]
                                # 检查选项是否包含"其他"或需要填空
                                try:
                                    label_text = selected_option.find_element(By.XPATH, '..//..//div[@class="label"]').text
                                    if '其他' in label_text or '请说明' in label_text or '请注明' in label_text:
                                        # 从有效选项中移除这个选项
                                        valid_options.pop(selected_index)
                                        valid_weights.pop(selected_index)
                                        continue
                                except:
                                    pass
                                
                                # 检查是否是"其他"选项
                                is_other_option = self._is_other_option(selected_option)
                                
                                # 对于多选题，尝试点击可见的UI元素
                                try:
                                    # 如果是隐藏的input，需要点击其可见的UI元素
                                    if selected_option.tag_name == 'input' and selected_option.get_attribute('style') == 'display:none;':
                                        # 查找可见的UI元素
                                        try:
                                            # 尝试查找可见的复选框UI
                                            visible_checkbox = selected_option.find_element(By.XPATH, '..//a[contains(@class, "checkbox")]')
                                            self.driver.execute_script("arguments[0].click();", visible_checkbox)
                                            print("点击了可见的复选框UI")
                                        except:
                                            # 如果找不到可见UI，尝试点击父元素
                                            parent = selected_option.find_element(By.XPATH, '..')
                                            self.driver.execute_script("arguments[0].click();", parent)
                                            print("点击了父元素")
                                    else:
                                        # 直接点击可见元素（缩短等待时间）
                                        self._click_option(selected_option, is_multi=True)
                                    
                                    time.sleep(0.2)
                                    
                                    # 验证是否选中
                                    if self._is_option_selected(selected_option):
                                        print("选项已成功选中")
                                        
                                        # 如果是"其他"选项，需要填写补充内容
                                        if is_other_option:
                                            question_element = self.driver.find_element(By.XPATH, f'//div[@id="div{question_index}"]')
                                            self._fill_other_option_text(question_element)
                                    else:
                                        print("选项可能未选中，尝试其他方法")
                                        
                                except Exception as e:
                                    print(f"点击多选题选项失败: {e}")
                                selected_count += 1
                                
                                # 从有效选项中移除已选择的选项
                                valid_options.pop(selected_index)
                                valid_weights.pop(selected_index)
                                
                                time.sleep(random.uniform(0.1, 0.3))
            
            # 如果没有权重设置或权重都为0，随机选择
            if selected_count == 0:
                for _ in range(max_selections):
                    if not options:
                        break
                    
                    option = random.choice(options)
                    # 检查选项是否包含"其他"或需要填空
                    try:
                        label_text = option.find_element(By.XPATH, '..//..//div[@class="label"]').text
                        if '其他' in label_text or '请说明' in label_text or '请注明' in label_text:
                            options.remove(option)
                            continue
                    except:
                        pass
                    
                    # 检查是否是"其他"选项
                    is_other_option = self._is_other_option(option)
                    
                    # 对于多选题，尝试点击可见的UI元素
                    try:
                        # 如果是隐藏的input，需要点击其可见的UI元素
                        if option.tag_name == 'input' and option.get_attribute('style') == 'display:none;':
                            # 查找可见的UI元素
                            try:
                                # 尝试查找可见的复选框UI
                                visible_checkbox = option.find_element(By.XPATH, '..//a[contains(@class, "checkbox")]')
                                self.driver.execute_script("arguments[0].click();", visible_checkbox)
                                print("点击了可见的复选框UI")
                            except:
                                # 如果找不到可见UI，尝试点击父元素
                                parent = option.find_element(By.XPATH, '..')
                                self.driver.execute_script("arguments[0].click();", parent)
                                print("点击了父元素")
                        else:
                            # 直接点击可见元素（缩短等待时间）
                            self._click_option(option, is_multi=True)
                        
                        time.sleep(0.2)
                        
                        # 验证是否选中
                        if self._is_option_selected(option):
                            print("选项已成功选中")
                            
                            # 如果是"其他"选项，需要填写补充内容
                            if is_other_option:
                                question_element = self.driver.find_element(By.XPATH, f'//div[@id="div{question_index}"]')
                                self._fill_other_option_text(question_element)
                        else:
                            print("选项可能未选中，尝试其他方法")
                            
                    except Exception as e:
                        print(f"点击多选题选项失败: {e}")
                    
                    selected_count += 1
                    options.remove(option)
                    time.sleep(random.uniform(0.1, 0.3))
            
            print(f"多选题第{question_index}题选择了{selected_count}个选项")
            return True
            
        except Exception as e:
            print(f"多选题第{question_index}题处理失败: {e}")
            self._save_failure_screenshot(f"multi_choice_{question_index}_error", f"多选题第{question_index}题处理失败: {e}")
            return False 

    def _is_other_option(self, option):
        """检查是否是"其他"选项"""
        try:
            # 尝试多种方式检查选项文本
            selectors = [
                '..//..//div[@class="label"]',
                '..//div[@class="label"]',
                '..//span[@class="label"]',
                '..//div[contains(@class, "label")]',
                '..//span[contains(@class, "label")]',
                '..//..//div[contains(@class, "label")]',
                '..//..//span[contains(@class, "label")]'
            ]
            
            for selector in selectors:
                try:
                    label_element = option.find_element(By.XPATH, selector)
                    label_text = label_element.text.strip()
                    if any(keyword in label_text for keyword in ['其他', '请说明', '请注明', '请填写', '请描述']):
                        print(f"检测到'其他'选项: {label_text}")
                        return True
                except:
                    continue
            
            return False
        except Exception as e:
            print(f"检查'其他'选项时出错: {e}")
            return False

    def _fill_other_option_text(self, question_element):
        """填写"其他"选项的补充文本"""
        try:
            # 查找可能的文本输入框
            text_input_selectors = [
                './/input[@type="text"]',
                './/textarea',
                './/input[contains(@class, "text")]',
                './/input[contains(@class, "input")]',
                './/div[contains(@class, "text")]//input',
                './/div[contains(@class, "input")]//input'
            ]
            
            for selector in text_input_selectors:
                try:
                    text_inputs = question_element.find_elements(By.XPATH, selector)
                    for text_input in text_inputs:
                        if text_input.is_displayed() and text_input.is_enabled():
                            # 生成合适的文本
                            if self.use_ai:
                                # 使用AI生成文本
                                question_text = question_element.find_element(By.XPATH, './/div[@class="field-label"]').text
                                ai_text = self.ai_generator.generate_answer(f"请为问卷中的'其他'选项生成一个合理的补充说明，问题：{question_text}")
                                text_input.clear()
                                text_input.send_keys(ai_text)
                                print(f"AI生成了'其他'选项文本: {ai_text}")
                            else:
                                # 使用默认文本
                                default_text = "无特殊说明"
                                text_input.clear()
                                text_input.send_keys(default_text)
                                print(f"填写了默认'其他'选项文本: {default_text}")
                            
                            time.sleep(0.5)
                            return True
                except Exception as e:
                    print(f"查找文本输入框失败 {selector}: {e}")
                    continue
            
            print("未找到'其他'选项的文本输入框")
            return False
        except Exception as e:
            print(f"填写'其他'选项文本时出错: {e}")
            return False

    def _remove_shade(self):
        """移除遮罩层"""
        try:
            # 尝试移除可能的遮罩层
            shade_elements = self.driver.find_elements(By.CSS_SELECTOR, '.layui-layer-shade, .modal-backdrop, .overlay')
            for shade in shade_elements:
                self.driver.execute_script("arguments[0].remove();", shade)
        except:
            pass 