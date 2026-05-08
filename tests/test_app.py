import os
import time
import pytest
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

APP_URL = os.getenv("APP_URL", "http://localhost:5000")

@pytest.fixture(scope="module")
def driver():
    # Clear database before tests
    db_path = "src/app.db" if os.path.exists("src/app.db") else "app.db"
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('DELETE FROM users')
        conn.commit()
        conn.close()
    except Exception as e:
        pass
        
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(5)
    
    yield driver
    driver.quit()

def test_1_page_title(driver):
    driver.get(APP_URL)
    assert "User Registry" in driver.title

def test_2_main_header(driver):
    driver.get(APP_URL)
    header = driver.find_element(By.ID, "main-header")
    assert header.text == "User Registry Dashboard"

def test_3_add_user_form_present(driver):
    driver.get(APP_URL)
    assert driver.find_element(By.ID, "name-input").is_displayed()
    assert driver.find_element(By.ID, "email-input").is_displayed()
    assert driver.find_element(By.ID, "submit-btn").is_displayed()

def test_4_users_table_present(driver):
    driver.get(APP_URL)
    assert driver.find_element(By.ID, "users-table").is_displayed()

def test_5_name_field_is_required(driver):
    driver.get(APP_URL)
    name_input = driver.find_element(By.ID, "name-input")
    assert name_input.get_attribute("required") == "true"

def test_6_email_field_is_required(driver):
    driver.get(APP_URL)
    email_input = driver.find_element(By.ID, "email-input")
    assert email_input.get_attribute("required") == "true"

def test_7_add_new_user(driver):
    driver.get(APP_URL)
    driver.find_element(By.ID, "name-input").send_keys("John Doe")
    driver.find_element(By.ID, "email-input").send_keys("john@example.com")
    driver.find_element(By.ID, "submit-btn").click()
    
    # Wait for page reload
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "users-table")))
    page_source = driver.page_source
    assert "John Doe" in page_source
    assert "john@example.com" in page_source

def test_8_add_second_user(driver):
    driver.get(APP_URL)
    driver.find_element(By.ID, "name-input").send_keys("Jane Smith")
    driver.find_element(By.ID, "email-input").send_keys("jane@example.com")
    driver.find_element(By.ID, "submit-btn").click()
    
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "users-table")))
    page_source = driver.page_source
    assert "Jane Smith" in page_source

def test_9_verify_multiple_users_in_list(driver):
    driver.get(APP_URL)
    user_rows = driver.find_elements(By.CLASS_NAME, "user-row")
    assert len(user_rows) >= 2

def test_10_search_existing_user(driver):
    driver.get(APP_URL)
    search_input = driver.find_element(By.ID, "search-input")
    search_input.send_keys("Jane")
    driver.find_element(By.ID, "search-btn").click()
    
    user_rows = driver.find_elements(By.CLASS_NAME, "user-row")
    assert len(user_rows) == 1
    assert "Jane Smith" in user_rows[0].text
    assert "John Doe" not in user_rows[0].text

def test_11_search_non_existing_user(driver):
    driver.get(APP_URL)
    search_input = driver.find_element(By.ID, "search-input")
    search_input.send_keys("Ghost")
    driver.find_element(By.ID, "search-btn").click()
    
    msg = driver.find_element(By.ID, "no-users-msg")
    assert msg.is_displayed()
    assert "No users found" in msg.text

def test_12_clear_search_results(driver):
    driver.get(APP_URL)
    driver.find_element(By.ID, "clear-search-btn").click()
    
    user_rows = driver.find_elements(By.CLASS_NAME, "user-row")
    # Should show all users again
    assert len(user_rows) >= 2

def test_13_edit_user_name(driver):
    driver.get(APP_URL)
    # Find the row for Jane Smith to edit
    rows = driver.find_elements(By.CLASS_NAME, "user-row")
    edit_input = None
    edit_btn = None
    for row in rows:
        if "Jane Smith" in row.text:
            edit_input = row.find_element(By.CLASS_NAME, "edit-input")
            edit_btn = row.find_element(By.XPATH, ".//button[text()='Edit']")
            break
            
    assert edit_input is not None
    edit_input.send_keys("Jane Williams")
    edit_btn.click()
    
    # Wait for page reload
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "users-table")))
    
def test_14_verify_edited_name(driver):
    driver.get(APP_URL)
    page_source = driver.page_source
    assert "Jane Williams" in page_source
    assert "Jane Smith" not in page_source

def test_15_delete_user(driver):
    driver.get(APP_URL)
    # Find the delete button for John Doe
    rows = driver.find_elements(By.CLASS_NAME, "user-row")
    delete_btn = None
    for row in rows:
        if "John Doe" in row.text:
            delete_btn = row.find_element(By.CLASS_NAME, "delete-btn")
            break
            
    assert delete_btn is not None
    delete_btn.click()
    
    # Wait for reload
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "users-table")))
    page_source = driver.page_source
    assert "John Doe" not in page_source
