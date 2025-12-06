# 这是对survey_filler.py的修复说明
# 主要问题：多页问卷需要处理"下一页"按钮，而不是直接提交

# 修复方案：
# 1. 在fill_survey函数中添加多页处理逻辑
# 2. 检测是否存在"下一页"按钮，如果存在则点击而不是提交
# 3. 循环处理每一页，直到最后一页才提交

# 关键修改点：

# 在 fill_survey 函数的最后，替换原有的提交逻辑：

"""
原代码：
            # 查找并点击提交按钮
            submit_result = self._find_and_submit()
            if not submit_result:
                self._save_failure_screenshot("submit_failed", "提交按钮点击失败或提交后未成功")
            return submit_result

新代码：
            # 处理多页问卷
            page_count = 1
            max_pages = 20  # 防止无限循环
            
            while page_count <= max_pages:
                print(f"\n========== 处理第 {page_count} 页 ==========")
                
                # 检查是否存在"下一页"按钮
                next_button = self._find_next_button()
                
                if next_button:
                    # 存在下一页，点击下一页按钮
                    print(f"检测到下一页按钮，准备点击...")
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                        time.sleep(0.5)
                        next_button.click()
                        print(f"已点击下一页按钮")
                        time.sleep(2)  # 等待页面加载
                        page_count += 1
                        
                        # 继续处理下一页的问题
                        try:
                            questions = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_all_elements_located((By.CLASS_NAME, 'field'))
                            )
                            print(f"第 {page_count} 页找到 {len(questions)} 个问题")
                            
                            for idx, question in enumerate(questions, 1):
                                try:
                                    if not question.is_displayed():
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
                                    
                                    time.sleep(1)
                                except Exception as e:
                                    print(f"处理第{idx}题时出错: {str(e)}")
                                    continue
                        except Exception as e:
                            print(f"加载第 {page_count} 页问题失败: {e}")
                            break
                    except Exception as e:
                        print(f"点击下一页按钮失败: {e}")
                        break
                else:
                    # 不存在下一页，说明已到最后一页，执行提交
                    print(f"未检测到下一页按钮，准备提交问卷...")
                    submit_result = self._find_and_submit()
                    if not submit_result:
                        self._save_failure_screenshot("submit_failed", "提交按钮点击失败或提交后未成功")
                    return submit_result
            
            print(f"超过最大页数限制 ({max_pages})，停止处理")
            return False
"""

# 新增函数：查找下一页按钮

"""
def _find_next_button(self):
    '''查找下一页按钮'''
    try:
        # 问卷星的下一页按钮通常有以下几种选择器
        selectors = [
            (By.ID, 'ctlNext'),  # 问卷星常用ID
            (By.CSS_SELECTOR, 'a.btn-next'),
            (By.CSS_SELECTOR, 'button.btn-next'),
            (By.XPATH, '//a[contains(text(), "下一页")]'),
            (By.XPATH, '//button[contains(text(), "下一页")]'),
            (By.CSS_SELECTOR, '.next-btn'),
            (By.CSS_SELECTOR, '[class*="next"]'),
            (By.XPATH, '//a[@id="ctlNext"]'),
            (By.XPATH, '//input[@value="下一页"]'),
        ]
        
        for selector in selectors:
            try:
                button = self.driver.find_element(*selector)
                if button and button.is_displayed() and button.is_enabled():
                    print(f"找到下一页按钮: {selector}")
                    return button
            except:
                continue
        
        print("未找到下一页按钮")
        return None
    except Exception as e:
        print(f"查找下一页按钮时出错: {e}")
        return None
"""

print("修复说明已生成，请按照上述说明修改survey_filler.py")
