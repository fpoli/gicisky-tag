import contextlib
from time import sleep

from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from dataline_starts import data_line_start_coords

USERNAME = ""
PASSWORD = ""

ip = "http://a.picksmart.cn:8081"

with contextlib.closing(webdriver.Firefox()) as driver:

    timeout = 3

    # Login
    driver.get(ip)
    wait = WebDriverWait(driver, 10)  # timeout after 10 seconds
    username = driver.find_element(By.XPATH, "//input[@placeholder='User Name']")
    username.send_keys(USERNAME)

    password = driver.find_element(By.XPATH, "//input[@placeholder='password']")
    password.send_keys(PASSWORD)

    code = driver.find_element(By.XPATH, "//input[@placeholder='code']")
    code.send_keys("")
    sleep(10)

    driver.get("http://a.picksmart.cn:8081/temp/edit/10261")

    wait.until(expected_conditions.presence_of_element_located((By.XPATH, "//input[@placeholder='Please select']")))

    tag_type = driver.find_element(By.XPATH, "//input[@placeholder='Please select']")
    tag_type.click()

    our_tag = '4.2"@EPA-B/W/R'
    our_tag_menu_option = driver.find_element(By.XPATH, f"//span[contains(text(), '{our_tag}')]")
    our_tag_menu_option.click()

    add_rectangle_button = driver.find_element(By.XPATH, f"//div[contains(text(), 'Rectangle')]")
    add_rectangle_button.click()

    first_rectangle = driver.find_element(By.XPATH, '//*[@id="app"]/div/div[2]/section/div/div[2]/div[2]/div[1]/div/div/div/div/div/div[1]/div')
    first_rectangle.click()

    copy_button = driver.find_element(By.XPATH, f"//span[contains(text(), 'Copy')]")
    save_button = driver.find_element(By.XPATH, f"//span[contains(text(), 'Save')]")

    X_pos = driver.find_element(By.XPATH, "//input[@placeholder='X']")
    Y_pos = driver.find_element(By.XPATH, "//input[@placeholder='Y']")

    width = driver.find_element(By.XPATH, "//input[@placeholder='Width']")
    height = driver.find_element(By.XPATH, "//input[@placeholder='Height']")
    width.clear()
    width.send_keys("1")
    height.clear()
    height.send_keys("1")

    for y, x in data_line_start_coords:
        copy_button.click()
        X_pos.clear()
        X_pos.send_keys(str(x))
        Y_pos.clear()
        Y_pos.send_keys(str(y))
        sleep(.1)

    # for x in range(0, 402, 2):
    #     y = 0
    #     # for y in range(0, 302, 2):
    #     copy_button.click()
    #     X_pos.clear()
    #     X_pos.send_keys(str(x))
    #     Y_pos.clear()
    #     Y_pos.send_keys(str(y))
    #     sleep(.1)
    #
    # for x in range(0, 112, 2):
    #     y = 1
    #     # for y in range(0, 302, 2):
    #     copy_button.click()
    #     X_pos.clear()
    #     X_pos.send_keys(str(x))
    #     Y_pos.clear()
    #     Y_pos.send_keys(str(y))
    #     sleep(.1)

    copy_button.click()
    save_button.click()

    filename_field = add_rectangle_button = driver.find_element(By.XPATH, "/html/body/div[3]/div/div[2]/div[2]/div[1]/input")
    filename_field.clear()
    filename_field.send_keys("FirstPixelofEachDataline")
    filename_field.send_keys(Keys.RETURN)

    sleep(10)
