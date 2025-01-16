import glob
import os
import threading
import time

from nicegui import app, ui, run

from main_local import txt_to_excel

# # make sure to call this method before creating any UI components
# from nicegui_toolkit import inject_layout_tool
# inject_layout_tool()


UPLOAD_DIR = os.path.join('./static', 'temp')
OUTPUT_EXCEL = os.path.join('./static', 'result.xlsx')
os.makedirs(UPLOAD_DIR, exist_ok=True)
stored_file_list = []
button_delete_list = []

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


# Function to delete files older than a certain time
def delete_old_files():
    refresh_items()

    current_time = time.time()
    for file in stored_file_list:
        if os.path.getmtime(file) < current_time - 60 * 10:  # 1 hour ago
            os.remove(file)
            print(f"Delete file: {file}")

    refresh_items()

    # Set the timer to run again in 1 hour
    threading.Timer(60 * 3, delete_old_files).start()


# disable the items
def disable_GUI_items():
    refresh_items()
    upload_files.disable()
    button_delete_all.disable()
    button_sequence.disable()
    button_process.disable()
    for button in button_delete_list:
        button.disable()


# enable the items
def enable_GUI_items():
    refresh_items()
    upload_files.enable()
    button_delete_all.enable()
    button_sequence.enable()
    button_process.enable()
    for button in button_delete_list:
        button.enable()


def refresh_items():
    refresh_stored_file_list()
    refresh_table_files()
    refresh_button_delete()


# use async to keep web GUI alive, put GUI control in this function, use await for backend computation
async def async_callback_button_process():
    refresh_items()
    if not stored_file_list:
        ui.notify('请先上传文件', color='red')
        return

    # disable the items
    disable_GUI_items()

    try:
        merged_df = await run.cpu_bound(txt_to_excel, stored_file_list)
        merged_df.to_excel(OUTPUT_EXCEL, index=False, engine='openpyxl')  # 使用 openpyxl 保存为 Excel
        ui.download(OUTPUT_EXCEL)
        ui.notify('Excel 文件已生成并可下载')
    except:
        ui.notify('出现了一些问题...', color='red')
        callback_button_delete_all()

    # enable the items
    enable_GUI_items()


# trigger everytime when each file is uploaded
def callback_upload_file(event):
    temp = event.content.read()
    # 限制文件类型和大小
    if not event.name.endswith('.txt'):
        ui.notify(f'文件 {event.name} 类型错误，仅支持 .txt 文件', color='red')
        upload_files.reset()
        return
    if len(temp) > 5 * 1024 * 1024:
        ui.notify(f'文件 {event.name} 超过了 5MB 大小限制', color='red')
        upload_files.reset()
        return
    # 限制文件数量
    refresh_items()
    if len(stored_file_list) >= 20:
        ui.notify(f'文件数量超过限制', color='red')
        upload_files.reset()
        return

    # save file
    file_path = os.path.join(UPLOAD_DIR, event.name)
    with open(file_path, 'wb') as f:
        f.write(temp)
    ui.notify(f'已上传文件: [{event.name}]')
    upload_files.reset()

    # update the table and button
    refresh_items()

    # enable the items
    button_process.enable()


def callback_button_sequence():
    refresh_items()
    ui.notify(f'文件顺序: {[os.path.basename(f) for f in stored_file_list]}')


def callback_button_delete_all():
    for file in os.listdir(UPLOAD_DIR):
        os.remove(os.path.join(UPLOAD_DIR, file))
    ui.notify('所有上传的文件已清空', color='green')

    # update the table and button
    upload_files.reset()
    refresh_items()


def callback_delete_file(file_path):
    os.remove(file_path)
    ui.notify(f'文件 {os.path.basename(file_path)} 已删除')

    # update the table and button
    refresh_items()


def refresh_stored_file_list():
    global stored_file_list
    stored_file_list = glob.glob(os.path.join(UPLOAD_DIR, "*"))


def refresh_table_files():
    table_files.rows = [
        {'Index'    : i,  # 用索引表示对应的行，方便删除
         'File Name': os.path.basename(f),
         }
        for i, f in enumerate(stored_file_list, start=1)
    ]
    table_files.update()


def refresh_button_delete():
    button_delete_container.clear()
    global button_delete_list
    button_delete_list = []
    with button_delete_container:
        ui.space().style("padding-top:37px;")
        for i, f in enumerate(stored_file_list):
            button_delete = ui.button(f"删除", on_click=lambda file=f: callback_delete_file(file), color='red').style('margin-bottom: -4px;')
            button_delete_list.append(button_delete)


# define GUI items
with ui.card().style('max-width: 400px;').classes('container'):
    with ui.row().style('width: 100%; justify-content: center'):
        label_header = ui.label('请上传TXT文件以处理').classes("text-h4 text-center")

    with ui.row().style('width: 100%; justify-content: center'):
        upload_files = ui.upload(on_upload=lambda e: callback_upload_file(e), multiple=True, label="上传'.txt'文件")

with ui.card().style('max-width: 400px;').classes('container'):
    with ui.row().style('width: 100%; justify-content: center'):
        label_files = ui.label('文件管理').style('font-size: 20px;')

    with ui.row().style('width: 100%; justify-content: center'):
        with ui.column():
            table_files = ui.table(
                columns=[
                    {'name': 'Index', 'label': '索引', 'field': 'Index', 'align': 'center'},
                    {'name': 'File Name', 'label': '文件名', 'field': 'File Name', 'align': 'center'},
                ],
                rows=[],
                row_key='File Name'
            )
        button_delete_container = ui.column()  # for subbuttons of each

    with ui.row().style('width: 100%').classes('justify-between'):
        button_delete_all = ui.button('清空文件', on_click=callback_button_delete_all, color='red')
        button_sequence = ui.button('检查顺序', on_click=callback_button_sequence, color='yellow')
        button_process = ui.button('生成Excel', on_click=async_callback_button_process, color='blue')

if __name__ == '__main__':
    callback_button_delete_all()
    refresh_items()
    delete_old_files()
    ui.run(reload=False, host="0.0.0.0", port=5000)  # reload=False is necessary for pyinstaller
