import glob
import pandas as pd


def txt_to_excel(_txt_list):
    dataframes = []
    for i, txt in enumerate(_txt_list, start=1):
        print(f'Working on [{i}/{len(_txt_list)}]: {txt}')
        df = pd.read_csv(txt, sep='\t', header=0, index_col=False)
        if i == 1:
            dataframes = [df]
        else:
            df.columns = dataframes[0].columns  # 保持列名与第一个文件一致
            dataframes.append(df)  # 添加到列表中

    _merged_df = pd.concat(dataframes, ignore_index=True)
    return _merged_df


if __name__ == '__main__':
    excel_path = 'output.xlsx'
    txt_list = glob.glob('./**/*.txt', recursive=True)

    merged_df = txt_to_excel(txt_list)
    merged_df.to_excel(excel_path, index=False, engine='openpyxl')  # 使用 openpyxl 保存为 Excel
    print(f"已成功将数据保存到 {excel_path}")
