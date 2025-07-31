import streamlit as st
import pandas as pd
import json
import os

DATA_FILE = "data.json"

st.set_page_config(page_title="СКАТ-анализатор", layout="wide")
st.title("📊 Анализ двузначных чисел из Excel")

# Шаг 1: Загрузка Excel файлов
uploaded_files = st.file_uploader("Загрузите один или несколько файлов Excel (.xlsx)", type="xlsx", accept_multiple_files=True)

# Шаг 2: галочка СКАТ
is_skat = st.checkbox("Это СКАТ? (не учитывать последнее число в каждой строке)")

# Шаг 3: диапазон строк
col1, col2 = st.columns(2)
start_id = col1.text_input("Начальный номер строки (например, 003181):")
end_id = col2.text_input("Конечный номер строки (например, 003200):")

if st.button("Обработать"):
    if uploaded_files and start_id and end_id:
        all_rows = []
        for file in uploaded_files:
            df = pd.read_excel(file, dtype=str)
            for _, row in df.iterrows():
                id_str = row.iloc[0].strip()
                numbers = [int(x.strip()) for x in row.iloc[1:7]]
                if is_skat:
                    numbers = numbers[:-1]
                all_rows.append({"id": id_str, "values": numbers})

        filtered = [item for item in all_rows if start_id <= item["id"] <= end_id]

        counts = {}
        for item in filtered:
            for num in item["values"]:
                counts[num] = counts.get(num, 0) + 1
        counts = {num: cnt * 2 for num, cnt in counts.items()}

        groups = {}
        for item in filtered:
            for num in item["values"]:
                diff = abs(int(str(num)[0]) - int(str(num)[1]))
                groups.setdefault(diff, []).append(num)

        mirror_groups = {}
        for diff, nums in groups.items():
            unique_nums = sorted(set(nums))
            visited = set()
            group_result = []

            for num in unique_nums:
                if num in visited:
                    continue
                mirror = int(str(num)[::-1])
                cnt = counts.get(num, 0)
                if mirror != num and mirror in unique_nums:
                    cnt_mirror = counts.get(mirror, 0)
                    group_result.append({
                        "number": num, "count": cnt,
                        "mirror": mirror, "mirror_count": cnt_mirror
                    })
                    visited.add(num)
                    visited.add(mirror)
                else:
                    group_result.append({"number": num, "count": cnt})
                    visited.add(num)

            mirror_groups[diff] = group_result

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(mirror_groups, f, ensure_ascii=False, indent=2)

        st.success(f"Обработка завершена. Найдено строк в диапазоне: {len(filtered)}")
        for diff, items in mirror_groups.items():
            st.subheader(f"Группа с разностью цифр: {diff}")
            rows = []
            for item in items:
                if "mirror" in item:
                    rows.append({
                        "Число": item["number"],
                        "Количество": item["count"],
                        "Зеркальное число": item["mirror"],
                        "Количество зеркального": item["mirror_count"]
                    })
                else:
                    rows.append({
                        "Число": item["number"],
                        "Количество": item["count"],
                        "Зеркальное число": "",
                        "Количество зеркального": ""
                    })
            df_result = pd.DataFrame(rows)
            st.dataframe(df_result, use_container_width=True)
    else:
        st.warning("Пожалуйста, загрузите файлы и введите диапазон.")

st.header("✏ Редактирование сохранённых данных (data.json)")
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data_json = json.load(f)
    edited = st.text_area("Редактируйте JSON", json.dumps(data_json, indent=2, ensure_ascii=False), height=400)
    if st.button("Сохранить изменения"):
        try:
            new_data = json.loads(edited)
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(new_data, f, ensure_ascii=False, indent=2)
            st.success("Изменения успешно сохранены!")
        except json.JSONDecodeError:
            st.error("Ошибка в формате JSON. Проверьте внимательно.")
else:
    st.info("Файл data.json пока не создан.")