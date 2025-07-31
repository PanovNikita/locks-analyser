import streamlit as st
import pandas as pd
import json
import os

# Файлы для хранения данных
RAW_DATA_FILE = "raw_data.json"  # все строки из загруженных таблиц
RESULT_FILE = "mirror_groups.json"  # результаты обработки диапазона

st.set_page_config(page_title="СКАТ-анализатор", layout="wide")
st.title("📊 Анализ двузначных чисел из Excel")

# --- Управление исходными данными (raw_data) ---
st.header("1. Управление исходными данными")
cols = st.columns(2)
with cols[0]:
    uploaded_files = st.file_uploader(
        "Загрузите новые файлы Excel для добавления к данным", 
        type="xlsx", accept_multiple_files=True)
    if st.button("Добавить файлы к исходным данным"):
        # Загружаем или создаём файл raw_data.json
        raw_data = []
        if os.path.exists(RAW_DATA_FILE):
            with open(RAW_DATA_FILE, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        # Читаем новые файлы и объединяем
        for file in uploaded_files:
            df = pd.read_excel(file, dtype=str)
            for _, row in df.iterrows():
                id_str = row.iloc[0].strip()
                values = [int(x.strip()) for x in row.iloc[1:7]]
                # обновляем или добавляем
                existing = next((item for item in raw_data if item["id"] == id_str), None)
                if existing:
                    existing["values"] = values
                else:
                    raw_data.append({"id": id_str, "values": values})
        # Сохраняем raw_data
        with open(RAW_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=2)
        st.success(f"Исходных строк в данных: {len(raw_data)}")

with cols[1]:
    if os.path.exists(RAW_DATA_FILE):
        st.write(f"Исходных строк в данных: {len(json.load(open(RAW_DATA_FILE)))}")
    else:
        st.info("Исходные данные пока не загружены. Добавьте Excel-файлы слева.")

# --- Анализ диапазона ---
st.header("2. Анализ заданного диапазона")
# Параметры анализа
diff_col1, diff_col2 = st.columns(2)
is_skat = diff_col1.checkbox("Это СКАТ? (не учитывать последнее число в каждой строке)")
start_id = diff_col1.text_input("Начальный номер строки (например, 003181):")
end_id = diff_col2.text_input("Конечный номер строки (например, 003200):")

if st.button("Обработать диапазон"):
    if not os.path.exists(RAW_DATA_FILE):
        st.error("Сначала загрузите исходные данные!")
    elif not start_id or not end_id:
        st.warning("Введите начало и конец диапазона.")
    else:
        # Загружаем raw_data
        raw_data = json.load(open(RAW_DATA_FILE, "r", encoding="utf-8"))
        # Фильтруем по диапазону
        filtered = [item.copy() for item in raw_data if start_id <= item["id"] <= end_id]
        # Применяем опцию СКАТ
        if is_skat:
            for item in filtered:
                if len(item["values"]) > 1:
                    item["values"] = item["values"][:-1]
        # Подсчёт удвоенный
        counts = {}
        for item in filtered:
            for num in item["values"]:
                counts[num] = counts.get(num, 0) + 1
        counts = {num: cnt * 2 for num, cnt in counts.items()}
        # Группировка по разности цифр
        groups = {}
        for item in filtered:
            for num in item["values"]:
                diff = abs(int(str(num)[0]) - int(str(num)[1]))
                groups.setdefault(diff, []).append(num)
        # Поиск зеркальных и вывод всех чисел
        mirror_groups = {}
        for diff, nums in groups.items():
            unique_nums = sorted(set(nums))
            visited = set()
            grp = []
            for num in unique_nums:
                if num in visited:
                    continue
                mirror = int(str(num)[::-1])
                cnt = counts.get(num, 0)
                if mirror != num and mirror in unique_nums:
                    cnt_mirr = counts.get(mirror, 0)
                    grp.append({"number": num, "count": cnt, "mirror": mirror, "mirror_count": cnt_mirr})
                    visited.update({num, mirror})
                else:
                    grp.append({"number": num, "count": cnt})
                    visited.add(num)
            mirror_groups[diff] = grp
        # Сохраняем результат
        with open(RESULT_FILE, "w", encoding="utf-8") as f:
            json.dump(mirror_groups, f, ensure_ascii=False, indent=2)
        st.success(f"Найдено строк в диапазоне: {len(filtered)}")
        # Вывод таблиц
        for diff, items in mirror_groups.items():
            st.subheader(f"Группа с разностью цифр: {diff}")
            rows = []
            for it in items:
                row = {"Число": it["number"], "Количество": it["count"]}
                if "mirror" in it:
                    row["Зеркальное число"] = it["mirror"]
                    row["Кол-во зеркального"] = it["mirror_count"]
                else:
                    row["Зеркальное число"] = ""
                    row["Кол-во зеркального"] = ""
                rows.append(row)
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

# --- Редактор результатов ---
st.header("3. Редактирование результатов")
if os.path.exists(RESULT_FILE):
    data_json = json.load(open(RESULT_FILE, "r", encoding="utf-8"))
    edited = st.text_area("Редактируйте mirror_groups.json", json.dumps(data_json, indent=2, ensure_ascii=False), height=300)
    if st.button("Сохранить результаты"):
        try:
            new_data = json.loads(edited)
            with open(RESULT_FILE, "w", encoding="utf-8") as f:
                json.dump(new_data, f, ensure_ascii=False, indent=2)
            st.success("Результаты сохранены!")
        except json.JSONDecodeError:
            st.error("Неверный формат JSON.")
else:
    st.info("Результаты ещё не сохранены. Сначала обработайте диапазон.")
