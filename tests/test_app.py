import pytest
import time
import sqlite3
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

APP_URL = os.environ.get('APP_URL', 'http://web:5000')
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src', 'elite_cars.db')

@pytest.fixture(scope='session')
def driver():
    """Set up a headless Chrome browser for the entire test session."""
    # Clean up test user data before running tests
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM rentals WHERE user_id IN (SELECT id FROM users WHERE username = 'testdriver')")
        conn.execute("DELETE FROM users WHERE username = 'testdriver'")
        conn.execute("UPDATE cars SET available = 1")
        conn.commit()
        conn.close()
    except Exception:
        pass  # DB might not exist locally

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    browser = webdriver.Chrome(options=options)
    browser.implicitly_wait(5)
    yield browser
    browser.quit()


# ==================== TEST 1: Login Page Title ====================
def test_1_login_page_title(driver):
    """Verify the login page loads with the correct title."""
    driver.get(f'{APP_URL}/login')
    assert 'Elite Car Rental' in driver.title


# ==================== TEST 2: Login Form Elements ====================
def test_2_login_form_elements_present(driver):
    """Verify that username, password fields and login button are present."""
    driver.get(f'{APP_URL}/login')
    assert driver.find_element(By.ID, 'username')
    assert driver.find_element(By.ID, 'password')
    assert driver.find_element(By.ID, 'login-btn')


# ==================== TEST 3: Signup Link Works ====================
def test_3_signup_link_navigation(driver):
    """Verify that clicking the signup link navigates to the signup page."""
    driver.get(f'{APP_URL}/login')
    signup_link = driver.find_element(By.ID, 'signup-link')
    signup_link.click()
    time.sleep(1)
    assert 'Sign Up' in driver.title or '/signup' in driver.current_url


# ==================== TEST 4: Signup Form Elements ====================
def test_4_signup_form_elements_present(driver):
    """Verify the signup page has all required form fields."""
    driver.get(f'{APP_URL}/signup')
    assert driver.find_element(By.ID, 'full_name')
    assert driver.find_element(By.ID, 'email')
    assert driver.find_element(By.ID, 'username')
    assert driver.find_element(By.ID, 'password')
    assert driver.find_element(By.ID, 'signup-btn')


# ==================== TEST 5: Register New User ====================
def test_5_register_new_user(driver):
    """Register a new user and verify redirect to login with success message."""
    driver.get(f'{APP_URL}/signup')
    driver.find_element(By.ID, 'full_name').send_keys('Test Driver')
    driver.find_element(By.ID, 'email').send_keys('testdriver@elite.com')
    driver.find_element(By.ID, 'username').send_keys('testdriver')
    driver.find_element(By.ID, 'password').send_keys('password123')
    driver.find_element(By.ID, 'signup-btn').click()
    time.sleep(1)
    assert '/login' in driver.current_url
    flash = driver.find_element(By.ID, 'flash-message')
    assert 'Account created' in flash.text


# ==================== TEST 6: Login with Registered User ====================
def test_6_login_with_valid_credentials(driver):
    """Login with the newly registered user and verify dashboard redirect."""
    driver.get(f'{APP_URL}/login')
    driver.find_element(By.ID, 'username').send_keys('testdriver')
    driver.find_element(By.ID, 'password').send_keys('password123')
    driver.find_element(By.ID, 'login-btn').click()
    time.sleep(1)
    assert '/dashboard' in driver.current_url


# ==================== TEST 7: Dashboard Loads After Login ====================
def test_7_dashboard_welcome_message(driver):
    """Verify the dashboard shows the user's full name in the welcome message."""
    title = driver.find_element(By.ID, 'dashboard-title')
    assert 'Test Driver' in title.text


# ==================== TEST 8: Cars List Visible ====================
def test_8_cars_grid_displays_cars(driver):
    """Verify the cars grid shows available car cards on the dashboard."""
    cars_grid = driver.find_element(By.ID, 'cars-grid')
    car_cards = cars_grid.find_elements(By.CLASS_NAME, 'car-card')
    assert len(car_cards) >= 1


# ==================== TEST 9: Search for a Car ====================
def test_9_search_car_by_brand(driver):
    """Search for 'BMW' and verify only matching results appear."""
    driver.get(f'{APP_URL}/dashboard')
    search_input = driver.find_element(By.ID, 'search-input')
    search_input.clear()
    search_input.send_keys('BMW')
    driver.find_element(By.ID, 'search-btn').click()
    time.sleep(1)
    car_cards = driver.find_elements(By.CLASS_NAME, 'car-card')
    assert len(car_cards) >= 1
    for card in car_cards:
        text = card.text.upper()
        assert 'BMW' in text


# ==================== TEST 10: Clear Search ====================
def test_10_clear_search_restores_all_cars(driver):
    """Click clear search and verify all cars are restored."""
    driver.find_element(By.ID, 'clear-search').click()
    time.sleep(1)
    car_cards = driver.find_elements(By.CLASS_NAME, 'car-card')
    assert len(car_cards) >= 5


# ==================== TEST 11: Rent a Car ====================
def test_11_rent_a_car(driver):
    """Rent the first available car and verify redirect to My Rentals."""
    driver.get(f'{APP_URL}/dashboard')
    time.sleep(1)
    first_car = driver.find_elements(By.CLASS_NAME, 'rent-btn')[0]
    first_car.click()
    time.sleep(1)
    assert '/my-rentals' in driver.current_url
    flash = driver.find_element(By.ID, 'flash-message')
    assert 'rented successfully' in flash.text


# ==================== TEST 12: View Rented Cars ====================
def test_12_rental_appears_in_my_rentals(driver):
    """Verify the rented car appears in the My Rentals table."""
    table = driver.find_element(By.ID, 'rentals-table')
    rows = table.find_elements(By.TAG_NAME, 'tr')
    assert len(rows) >= 2  # header + at least one rental row
    assert 'Active' in table.text


# ==================== TEST 13: Return a Car ====================
def test_13_return_rented_car(driver):
    """Click the Return button and verify the car is returned."""
    return_btns = driver.find_elements(By.CSS_SELECTOR, '[id^="return-btn-"]')
    assert len(return_btns) >= 1
    return_btns[0].click()
    time.sleep(1)
    flash = driver.find_element(By.ID, 'flash-message')
    assert 'returned successfully' in flash.text


# ==================== TEST 14: Edit Profile ====================
def test_14_update_user_profile(driver):
    """Navigate to profile, update the full name, and verify success message."""
    driver.get(f'{APP_URL}/profile')
    time.sleep(1)
    name_field = driver.find_element(By.ID, 'full_name')
    name_field.clear()
    name_field.send_keys('Test Driver Updated')
    driver.find_element(By.ID, 'update-btn').click()
    time.sleep(1)
    flash = driver.find_element(By.ID, 'flash-message')
    assert 'Profile updated' in flash.text


# ==================== TEST 15: Logout ====================
def test_15_logout_redirects_to_login(driver):
    """Click logout and verify redirect back to the login page."""
    driver.get(f'{APP_URL}/logout')
    time.sleep(1)
    assert '/login' in driver.current_url
    assert driver.find_element(By.ID, 'login-btn')
