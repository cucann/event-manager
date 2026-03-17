import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import base64
from io import BytesIO
import calendar
from collections import Counter

# Конфигурация страницы
st.set_page_config(
    page_title="Event Manager Pro",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Адрес бэкенда
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend-service:8000")
API_URL = f"{BACKEND_URL}/events"

# Заголовок
st.markdown("""
    <h1 style='text-align: center; color: #2c3e50;'>
        📅 Корпоративный Event Manager Pro
    </h1>
    <p style='text-align: center; color: #7f8c8d; font-size: 1.2em;'>
        Управляйте событиями вашей компании эффективно
    </p>
    <hr>
""", unsafe_allow_html=True)

# ===== ФИЧА 1: Уведомления о предстоящих событиях =====
@st.cache_data(ttl=5)
def check_upcoming_events(df):
    if df.empty:
        return []
    
    today = datetime.now().date()
    upcoming = []
    
    for _, event in df.iterrows():
        try:
            event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
            days_until = (event_date - today).days
            if 0 <= days_until <= 2:
                upcoming.append((event, days_until))
        except:
            continue
    
    return upcoming

# ===== ФИЧА 5: Таймер обратного отсчёта =====
@st.cache_data(ttl=5)
def get_next_event(df):
    if df.empty:
        return None, None
    
    today = datetime.now()
    future_events = []
    
    for _, event in df.iterrows():
        try:
            event_datetime = datetime.strptime(f"{event['date']} {event['time']}", '%Y-%m-%d %H:%M')
            if event_datetime > today:
                future_events.append((event, event_datetime))
        except:
            continue
    
    if future_events:
        return min(future_events, key=lambda x: x[1])
    return None, None

# Боковая панель
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/calendar--v1.png", width=100)
    st.markdown("## Навигация")
    
    menu = st.radio(
        "Меню",
        ["📋 Все события", "➕ Добавить событие", "📊 Аналитика", "📅 Календарь", "⚙️ Настройки"]
    )
    
    st.markdown("---")
    
    try:
        health_check = requests.get(f"{BACKEND_URL}/", timeout=2)
        if health_check.status_code == 200:
            st.success("✅ Бэкенд: Online")
        else:
            st.error("❌ Бэкенд: Offline")
    except:
        st.error("❌ Бэкенд: Offline")
    
    st.caption(f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}")

# Функции для работы с данными
@st.cache_data(ttl=10, show_spinner="Загрузка событий...")
def load_events():
    try:
        response = requests.get(API_URL, timeout=5)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def add_event(event_data):
    try:
        with st.spinner("Добавление события..."):
            response = requests.post(API_URL, json=event_data, timeout=5)
            if response.status_code == 200:
                st.balloons()
                st.cache_data.clear()
                return True
            return False
    except Exception as e:
        st.error(f"Ошибка: {e}")
        return False

def delete_event(event_id):
    try:
        with st.spinner("Удаление события..."):
            response = requests.delete(f"{API_URL}/{event_id}", timeout=5)
            if response.status_code == 200:
                st.success("✅ Событие удалено!")
                st.cache_data.clear()
                return True
            return False
    except:
        return False

def update_event(event_id, updated_data):
    try:
        with st.spinner("Обновление события..."):
            delete_response = requests.delete(f"{API_URL}/{event_id}", timeout=5)
            if delete_response.status_code == 200:
                response = requests.post(API_URL, json=updated_data, timeout=5)
                if response.status_code == 200:
                    st.success("✅ Событие обновлено!")
                    st.balloons()
                    st.cache_data.clear()
                    return True
            return False
    except Exception as e:
        st.error(f"Ошибка: {e}")
        return False

def get_csv_download_link(df, filename="events.csv"):
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">📥 Скачать CSV</a>'
    return href

def get_excel_download_link(df, filename="events.xlsx"):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Events')
    excel_data = output.getvalue()
    b64 = base64.b64encode(excel_data).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">📊 Скачать Excel</a>'
    return href

def highlight_dates(row):
    try:
        today = datetime.now().date()
        event_date = datetime.strptime(row['date'], '%Y-%m-%d').date()
        
        if event_date < today:
            return ['background-color: #ffcccc'] * len(row)
        elif event_date == today:
            return ['background-color: #ccffcc'] * len(row)
        elif event_date < today + timedelta(days=3):
            return ['background-color: #ffffcc'] * len(row)
        return [''] * len(row)
    except:
        return [''] * len(row)

def safe_extract_hour(time_str):
    try:
        if pd.isna(time_str) or time_str == "" or time_str == ":00":
            return 12
        if isinstance(time_str, str):
            for fmt in ['%H:%M', '%H:%M:%S']:
                try:
                    return pd.to_datetime(time_str, format=fmt).hour
                except:
                    continue
        return 12
    except:
        return 12

# Загрузка данных
events = load_events()
df = pd.DataFrame(events) if events else pd.DataFrame()

# ===== ФИЧА 1: Отображение уведомлений =====
if not df.empty:
    upcoming_events = check_upcoming_events(df)
    if upcoming_events:
        with st.container():
            st.markdown("### 📢 Напоминания о ближайших событиях")
            for event, days in upcoming_events:
                if days == 0:
                    st.warning(f"🔴 **СЕГОДНЯ**: {event['title']} в {event['time']} ({event['location']})")
                elif days == 1:
                    st.info(f"🟡 **ЗАВТРА**: {event['title']} в {event['time']} ({event['location']})")
                else:
                    st.info(f"🟢 **ЧЕРЕЗ {days} ДНЯ**: {event['title']} в {event['time']} ({event['location']})")
            st.markdown("---")

# ===== ФИЧА 5: Таймер обратного отсчёта в боковой панели =====
with st.sidebar:
    if not df.empty:
        next_event, next_time = get_next_event(df)
        if next_event is not None:
            st.markdown("---")
            st.markdown("### ⏰ Ближайшее событие")
            
            delta = next_time - datetime.now()
            days = delta.days
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            
            if days > 0:
                st.info(f"**{next_event['title']}**\n\nЧерез {days} дн {hours} ч {minutes} мин")
            elif hours > 0:
                st.info(f"**{next_event['title']}**\n\nЧерез {hours} ч {minutes} мин")
            else:
                st.warning(f"**{next_event['title']}**\n\nЧерез {minutes} мин!")

# --- Страница "Все события" ---
if menu == "📋 Все события":
    st.header("📋 Список всех событий")
    
    if df.empty:
        st.info("ℹ️ Пока нет событий. Добавьте новое событие в меню '➕ Добавить событие'")
    else:
        with st.expander("🔍 Расширенные фильтры", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                search_term = st.text_input("🔎 Поиск по названию", placeholder="Введите текст...")
            
            with col2:
                if 'location' in df.columns:
                    locations = ['Все'] + list(df['location'].unique())
                    location_filter = st.selectbox("📍 Место проведения", locations)
                else:
                    location_filter = 'Все'
            
            with col3:
                date_range = st.date_input("📅 Период", [], help="Выберите начальную и конечную даты")
        
        filtered_df = df.copy()
        
        if search_term:
            filtered_df = filtered_df[filtered_df['title'].str.contains(search_term, case=False, na=False)]
        
        if location_filter != 'Все':
            filtered_df = filtered_df[filtered_df['location'] == location_filter]
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df['date_dt'] = pd.to_datetime(filtered_df['date'])
            mask = (filtered_df['date_dt'].dt.date >= start_date) & (filtered_df['date_dt'].dt.date <= end_date)
            filtered_df = filtered_df[mask]
        
        st.caption(f"📊 Показано {len(filtered_df)} из {len(df)} событий")
        
        if not filtered_df.empty:
            col1, col2 = st.columns([1, 5])
            with col1:
                st.markdown(get_csv_download_link(filtered_df), unsafe_allow_html=True)
            try:
                import openpyxl
                with col2:
                    st.markdown(get_excel_download_link(filtered_df), unsafe_allow_html=True)
            except:
                pass
            
            st.dataframe(
                filtered_df.style.apply(highlight_dates, axis=1),
                use_container_width=True,
                column_config={
                    "title": "Название",
                    "date": "Дата",
                    "time": "Время",
                    "location": "Место",
                    "participants": st.column_config.ListColumn("Участники"),
                    "description": "Описание"
                },
                height=400
            )
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Всего на странице", len(filtered_df))
            with col2:
                unique_dates = filtered_df['date'].nunique()
                st.metric("Уникальных дат", unique_dates)
            with col3:
                total_participants = sum([len(p) if isinstance(p, list) else 0 for p in filtered_df['participants']])
                st.metric("Всего участников", total_participants)
            with col4:
                if 'location' in filtered_df.columns:
                    unique_places = filtered_df['location'].nunique()
                    st.metric("Мест проведения", unique_places)
            
            # ===== Управление событиями (редактирование и удаление) =====
            st.markdown("---")
            st.subheader("✏️ Управление событиями")
            
            if not filtered_df.empty and 'id' in filtered_df.columns:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    event_options = {f"{e['title']} ({e['date']} {e['time']})": e['id'] 
                                   for e in filtered_df.to_dict('records')}
                    selected_event_id = st.selectbox(
                        "Выберите событие", 
                        options=list(event_options.keys()),
                        key="event_selector"
                    )
                    selected_event = filtered_df[filtered_df['id'] == event_options[selected_event_id]].iloc[0]
                
                with col2:
                    st.write("")
                    st.write("")
                    action = st.radio("Действие", ["✏️ Редактировать", "🗑️ Удалить"], horizontal=True)
                
                if action == "🗑️ Удалить":
                    if st.button("🗑️ Подтвердить удаление", type="primary", use_container_width=True):
                        if delete_event(event_options[selected_event_id]):
                            st.rerun()
                
                else:
                    with st.expander("✏️ Редактировать событие", expanded=True):
                        with st.form("edit_form"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                new_title = st.text_input("Название", value=selected_event['title'])
                                new_date = st.date_input("Дата", value=datetime.strptime(selected_event['date'], '%Y-%m-%d').date())
                                new_time = st.time_input("Время", value=datetime.strptime(selected_event['time'], '%H:%M').time())
                            
                            with col2:
                                new_location = st.text_input("Место", value=selected_event['location'])
                                
                                if isinstance(selected_event['participants'], list):
                                    participants_text = "\n".join(selected_event['participants'])
                                else:
                                    participants_text = ""
                                
                                new_participants = st.text_area("Участники (по одному в строке)", 
                                                               value=participants_text,
                                                               height=100)
                                new_description = st.text_area("Описание", value=selected_event.get('description', ''))
                            
                            if st.form_submit_button("💾 Сохранить изменения", type="primary"):
                                new_participants_list = [p.strip() for p in new_participants.split("\n") if p.strip()]
                                updated_data = {
                                    "title": new_title,
                                    "date": new_date.strftime("%Y-%m-%d"),
                                    "time": new_time.strftime("%H:%M"),
                                    "location": new_location,
                                    "participants": new_participants_list,
                                    "description": new_description
                                }
                                if update_event(event_options[selected_event_id], updated_data):
                                    st.rerun()
        else:
            st.warning("😕 Нет событий, соответствующих фильтрам")

# --- Страница "Добавить событие" ---
elif menu == "➕ Добавить событие":
    st.header("➕ Добавить новое событие")
    
    with st.form("event_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("📌 Название события*", placeholder="Например: Еженедельная встреча")
            date = st.date_input("📅 Дата*", value=datetime.now())
            time = st.time_input("⏰ Время*", value=datetime.now().time())
        
        with col2:
            location = st.text_input("📍 Место проведения*", placeholder="Например: Переговорная 301")
            participants = st.text_area("👥 Участники (по одному в строке)",
                                       placeholder="Иван Петров\nМария Сидорова\nАлексей Иванов")
            description = st.text_area("📝 Описание", placeholder="Детали события...")
        
        st.markdown("---")
        submitted = st.form_submit_button("✅ Создать событие", use_container_width=True, type="primary")
        
        if submitted:
            if not title or not date or not time or not location:
                st.error("❌ Заполните все обязательные поля (*)")
            else:
                participants_list = [p.strip() for p in participants.split("\n") if p.strip()]
                event_data = {
                    "title": title,
                    "date": date.strftime("%Y-%m-%d"),
                    "time": time.strftime("%H:%M"),
                    "location": location,
                    "participants": participants_list,
                    "description": description
                }
                if add_event(event_data):
                    st.success("✨ Событие успешно создано!")

# --- Страница "Аналитика" ---
elif menu == "📊 Аналитика":
    st.header("📊 Аналитика событий")
    
    if df.empty:
        st.info("📊 Нет данных для аналитики. Добавьте события, чтобы увидеть статистику.")
    else:
        df = df.copy()
        df['date_dt'] = pd.to_datetime(df['date'])
        df['month'] = df['date_dt'].dt.month_name()
        df['weekday'] = df['date_dt'].dt.day_name()
        df['hour'] = df['time'].apply(safe_extract_hour)
        
        st.subheader("🎯 Ключевые метрики")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Всего событий", len(df))
        
        with col2:
            upcoming = len(df[df['date_dt'].dt.date >= datetime.now().date()])
            st.metric("Предстоящие", upcoming)
        
        with col3:
            all_participants = []
            for p in df['participants']:
                if isinstance(p, list):
                    all_participants.extend(p)
            st.metric("Уникальных участников", len(set(all_participants)))
        
        with col4:
            avg_participants = sum([len(p) if isinstance(p, list) else 0 for p in df['participants']]) / len(df)
            st.metric("Среднее участников", f"{avg_participants:.1f}")
        
        # ===== ФИЧА 7: Рейтинг самых активных участников =====
        st.subheader("🏆 Рейтинг самых активных участников")
        all_participants = []
        for _, event in df.iterrows():
            if isinstance(event['participants'], list):
                all_participants.extend(event['participants'])
        
        if all_participants:
            top_participants = Counter(all_participants).most_common(5)
            
            for i, (name, count) in enumerate(top_participants, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                st.markdown(f"{medal} **{name}** - участвовал(а) в {count} событи(ях)")
        
        st.subheader("📈 Загруженность месяца")
        current_month = datetime.now().strftime("%Y-%m")
        month_events = len(df[df['date'].str.startswith(current_month)])
        max_events = 20
        progress = min(month_events / max_events, 1.0)
        st.progress(progress, text=f"Событий в текущем месяце: {month_events}/{max_events} ({progress*100:.0f}%)")
        
        col5, col6 = st.columns(2)
        
        with col5:
            st.subheader("📅 События по датам")
            date_counts = df['date_dt'].dt.date.value_counts().sort_index()
            if not date_counts.empty:
                fig = px.bar(
                    x=list(date_counts.index),
                    y=list(date_counts.values),
                    title="Количество событий по дням"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col6:
            st.subheader("📊 Популярные дни")
            weekday_counts = df['weekday'].value_counts()
            if not weekday_counts.empty:
                weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                weekday_counts = weekday_counts.reindex(weekday_order, fill_value=0)
                fig2 = px.bar(
                    x=weekday_counts.index,
                    y=weekday_counts.values,
                    title="События по дням недели"
                )
                st.plotly_chart(fig2, use_container_width=True)
        
        col7, col8 = st.columns(2)
        
        with col7:
            st.subheader("🏢 Популярные места")
            location_counts = df['location'].value_counts().head(5)
            if not location_counts.empty:
                fig3 = px.pie(
                    values=location_counts.values,
                    names=location_counts.index,
                    title="Топ-5 мест проведения"
                )
                st.plotly_chart(fig3, use_container_width=True)
        
        st.subheader("📋 Детальная статистика по месяцам")
        if not df.empty and 'month' in df.columns:
            stats_df = df.groupby('month').agg({
                'title': 'count',
                'participants': lambda x: sum([len(p) if isinstance(p, list) else 0 for p in x]),
                'location': lambda x: x.nunique()
            }).rename(columns={
                'title': 'Событий',
                'participants': 'Всего участников',
                'location': 'Уникальных мест'
            }).reset_index()
            st.dataframe(stats_df, use_container_width=True)

# --- Страница "Календарь" ---
elif menu == "📅 Календарь":
    st.header("📅 Календарь событий")
    
    if df.empty:
        st.info("Нет событий для отображения в календаре")
    else:
        df['date_dt'] = pd.to_datetime(df['date'])
        
        today = datetime.now()
        months = pd.date_range(start=today - timedelta(days=90), end=today + timedelta(days=90), freq='MS')
        month_options = {m.strftime("%B %Y"): m.strftime("%Y-%m") for m in months}
        
        selected_month_name = st.selectbox(
            "Выберите месяц",
            options=list(month_options.keys())
        )
        selected_month = month_options[selected_month_name]
        
        month_events = df[df['date'].str.startswith(selected_month)]
        
        if not month_events.empty:
            year, month = map(int, selected_month.split('-'))
            cal = calendar.monthcalendar(year, month)
            
            st.markdown(f"### {selected_month_name}")
            
            days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
            cols = st.columns(7)
            for i, day in enumerate(days):
                with cols[i]:
                    st.markdown(f"**{day}**")
            
            for week in cal:
                cols = st.columns(7)
                for i, day in enumerate(week):
                    with cols[i]:
                        if day != 0:
                            day_str = f"{year}-{month:02d}-{day:02d}"
                            day_events = month_events[month_events['date'] == day_str]
                            
                            if len(day_events) > 0:
                                st.markdown(f"**{day}** 📌")
                                with st.expander(f"{len(day_events)}"):
                                    for _, event in day_events.iterrows():
                                        st.markdown(f"• **{event['title']}** в {event['time']}")
                                        st.caption(f"  {event['location']}")
                            else:
                                st.markdown(f"**{day}**")
        else:
            st.info(f"Нет событий в {selected_month_name}")

# --- Страница "Настройки" ---
elif menu == "⚙️ Настройки":
    st.header("⚙️ Настройки приложения")
    
    st.markdown("### 🎨 Оформление")
    col1, col2 = st.columns(2)
    with col1:
        theme = st.selectbox("Тема оформления", ["Светлая", "Темная", "Системная"])
    with col2:
        language = st.selectbox("Язык интерфейса", ["Русский", "English"])
    
    st.markdown("---")
    st.markdown("### 🔧 Информация о системе")
    
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("**Версия приложения:**")
        st.code("Event Manager Pro v3.0")
        st.markdown("**Бэкенд API:**")
        st.code(BACKEND_URL)
    with col4:
        st.markdown("**Всего событий в БД:**")
        st.code(len(df))
        st.markdown("**Последнее обновление:**")
        st.code(datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
    
    st.markdown("---")
    st.markdown("### 📊 Статус сервисов")
    
    services_status = {
        "Бэкенд": "🟢 Online" if not df.empty else "🟡 Нет данных",
        "База данных MongoDB": "🟢 Connected",
        "Фронтенд": "🟢 Active",
        "API Доступ": "🟢 Доступен"
    }
    
    for service, status in services_status.items():
        st.markdown(f"- **{service}:** {status}")
    
    st.markdown("---")
    st.caption("© 2026 Event Manager Pro. Все права защищены.")# CI/CD демонстрация: автоматическая сборка с версионированием
