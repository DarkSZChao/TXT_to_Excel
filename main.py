import glob
import pandas as pd
from main_local import txt_to_excel

import asyncio
import os
from tempfile import TemporaryDirectory
from nicegui import app, ui, run

# expose the background image dir
app.add_static_files("/static", "static")

# set background
ui.add_head_html("""
<style>
    body {
        background-image: url('/static/background.jpg');
        background-size: cover;
        background-position: center;
        margin: 0;
        font-family: Arial, sans-serif;
    }
    .container {
        background: rgba(255, 255, 255, 0.8);
        border-radius: 10px;
        padding: 20px;
        max-width: 400px;
        margin: auto;
        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
    }
    .centered {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 100vh;
    }
</style>
""")


# disable the items
def disable_GUI_items():
    upload_txt.disable()
    button_process.disable()


# enable the items
def enable_GUI_items():
    upload_txt.enable()
    button_process.enable()


UPLOAD_DIR = os.path.join('./static', 'temp')
OUTPUT_EXCEL = os.path.join('./static', 'result.xlsx')
os.makedirs(UPLOAD_DIR, exist_ok=True)
uploaded_txt_list = []


# use async to keep web GUI alive, put GUi control in this function, use await for backend computation
async def async_callback_button_process():
    # disable the items
    disable_GUI_items()

    if not uploaded_txt_list:
        ui.notify('请先上传文件', color='red')
        return

    try:
        merged_df = await run.cpu_bound(txt_to_excel, uploaded_txt_list)
        merged_df.to_excel(OUTPUT_EXCEL, index=False, engine='openpyxl')  # 使用 openpyxl 保存为 Excel
        ui.download(OUTPUT_EXCEL)
        ui.notify('Excel 文件已生成并可下载')
    except:
        ui.notify('出现了一些问题...')

    # enable the items
    enable_GUI_items()


def upload_file(event):
    file_path = os.path.join(UPLOAD_DIR, event.name)
    with open(file_path, 'wb') as f:
        f.write(event.content.read())
    uploaded_txt_list.append(file_path)
    ui.notify(f'已上传文件: [{event.name}]')

    # enable the items
    button_process.enable()


def clear_files():
    uploaded_txt_list.clear()
    upload_txt.clear()
    for file in os.listdir(UPLOAD_DIR):
        os.remove(os.path.join(UPLOAD_DIR, file))
    ui.notify('所有上传的文件已清空', color='green')


# define GUI items
with ui.card().style('max-width: 400px;').classes('container'):
    with ui.row().style('width: 100%; justify-content: center'):
        label_header = ui.label('请上传TXT文件以处理').classes("text-h4 text-center")

    with ui.row().style('width: 100%; justify-content: center'):
        upload_txt = ui.upload(on_upload=lambda e: upload_file(e), multiple=True, label="上传'.txt'文件")

    with ui.row().style('width: 100%').classes('justify-between'):
        button_clear = ui.button('清空文件', on_click=clear_files, color='red')
        button_process = ui.button('生成Excel', on_click=async_callback_button_process, color='blue')
        button_process.disable()

# with ui.card().style('max-width: 400px;').classes('container'):
#     with ui.row().style('width: 100%; justify-content: center'):
#         ui.label('文件管理').style('font-size: 20px;')
#     with ui.row().style('width: 100%; justify-content: center'):
#         file_table = ui.table(rows=[],
#                               row_key='File Name'
#                               )

if __name__ == '__main__':
    ui.run(reload=False, host="0.0.0.0", port=5000)  # reload=False is necessary for pyinstaller
