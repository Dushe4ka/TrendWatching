from aiogram.fsm.state import State, StatesGroup

# Состояния FSM
class CSVUpload(StatesGroup):
    waiting_for_file = State()

class SubscriptionStates(StatesGroup):
    waiting_for_category = State()

class RSSUpload(StatesGroup):
    waiting_for_category = State()
    waiting_for_rss = State()
    waiting_for_more_rss = State()

class TGUpload(StatesGroup):
    waiting_for_category = State()
    waiting_for_tg = State()
    waiting_for_more_tg = State()

class CustomStates(StatesGroup):
    analysis_query_category = State()
    analysis_query_input = State()
    analysis_daily_category = State()
    analysis_daily_date = State()
    analysis_weekly_category = State()
    analysis_weekly_date = State()

class AuthStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_code = State()
    waiting_for_password = State()
    waiting_for_delete_phone = State()

class SourcesManageStates(StatesGroup):
    viewing_sources = State()

# Новые состояния для управления Telegram каналами
class TelegramChannelStates(StatesGroup):
    waiting_for_digest_category = State()
    waiting_for_digest_time = State()
    waiting_for_digest_edit_time = State()
    waiting_for_digest_edit_category = State()
    editing_digest_time = State()
    editing_digest_category = State()