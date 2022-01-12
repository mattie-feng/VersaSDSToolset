from datetime import datetime
from py.xml import html
import pytest

driver = None


@pytest.mark.optionalhook
def pytest_html_results_table_header(cells):
    cells.insert(1, html.th('Description'))


@pytest.mark.optionalhook
def pytest_html_results_table_row(report, cells):
    cells.insert(1, html.td(report.description))


@pytest.mark.hookwrapper
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    report.description = str(item.function.__doc__)
    report.nodeid = report.nodeid.encode("utf-8").decode("unicode_escape")  # 设置编码显示中文

# def _capture_screenshot():
#     '''
#     截图保存为base64，展示到html中
#     :return:
#     '''
#     return driver.get_screenshot_as_base64()
#
# @pytest.fixture(scope='session', autouse=True)
# def browser(request):
#     global driver
#     if driver is None:
#         driver = webdriver.Firefox()
#
#     def end():
#         driver.quit()
#     request.addfinalizer(end)
#     return driver
