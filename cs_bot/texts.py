WELCOME = (
    "안녕하세요! 고객센터 봇입니다. 👤\n\n"
    "문의 카테고리를 선택해 주세요."
)

SELECT_CATEGORY = "📂 문의 카테고리를 먼저 선택해 주세요."

CATEGORY_SELECTED = "✅ *{label}* 카테고리가 선택되었습니다.\n이제 메시지를 보내주세요."

MESSAGE_SENT = "📩 메시지가 전달되었습니다."

TICKET_CLOSED_USER = (
    "✅ 문의가 종료되었습니다.\n"
    "추가 문의가 있으시면 언제든 메시지를 보내주세요."
)

TICKET_CLOSED_ADMIN = "✅ 티켓이 종료되었습니다. 유저에게 알림을 전송했습니다."

CONFIRM_CLOSE = "정말 문의를 종료하시겠습니까?"

CONFIRM_CLOSE_YES = "✅ 예, 종료합니다"
CONFIRM_CLOSE_NO = "❌ 아니오"

BANNED = ""  # 차단 유저는 응답 없음

AFTER_HOURS = (
    "⏰ *현재 운영시간이 아닙니다*\n"
    "_평일 {start} \\~ {end} \\(KST\\)_\n\n"
    "메시지는 정상 접수되며 운영시간에 순차 답변드립니다\\."
)

CANNOT_SEND_USER = "⚠️ 유저에게 메시지를 전송할 수 없습니다. (봇 차단 또는 계정 비활성화)"

TOPIC_DELETED = "⚠️ 기존 토픽이 삭제되어 새 토픽을 생성했습니다."

BAN_DONE = "🚫 유저 `{user_id}` 를 차단하고 티켓을 종료했습니다."
UNBAN_DONE = "✅ 유저 `{user_id}` 차단을 해제했습니다."
UNBAN_NOT_FOUND = "❌ 해당 유저는 차단 목록에 없습니다."
UNBAN_USAGE = "사용법: `/unban <user_id>`"

NOTE_SAVED = "📝 메모가 저장되었습니다."
NOTE_USAGE = "사용법: `/note <내용>`"

INFO_TEMPLATE = (
    "👤 *유저 정보*\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "🏷️ 이름: {full_name}\n"
    "🔗 유저네임: {username}\n"
    "🆔 ID: `{user_id}`\n"
    "🌐 언어: {lang}\n"
    "📂 카테고리: {category}\n"
    "📊 이전 문의: {archive_cnt}건{last_str}\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "{notes_section}"
)

PINNED_CARD = (
    "👤 *유저 정보*\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "🏷️ 이름: {full_name}\n"
    "🔗 유저네임: {username}\n"
    "🆔 ID: `{user_id}`\n"
    "🌐 언어: {lang}\n"
    "📂 카테고리: {category}\n"
    "📊 이전 문의: {archive_cnt}건{last_str}\n"
    "━━━━━━━━━━━━━━━━━━━━"
)

FAQ_CANDIDATE = (
    "💡 *FAQ 후보 감지*\n\n"
    "매칭 키워드: `{keywords}`\n\n"
    "답변 내용:\n{answer}"
)

FAQ_SENT = "✅ FAQ 답변을 유저에게 전송했습니다."
FAQ_IGNORED = "❌ FAQ 무시됨. 수동으로 응답해 주세요."

FAQ_ADD_USAGE = "사용법: `/faq_add <카테고리|*> <키워드1,키워드2> | <답변>`"
FAQ_ADD_DONE = "✅ FAQ #{faq_id} 추가되었습니다."
FAQ_DEL_DONE = "✅ FAQ #{faq_id} 삭제되었습니다."
FAQ_DEL_NOT_FOUND = "❌ 해당 FAQ가 없습니다."
FAQ_TOGGLE_DONE = "✅ FAQ #{faq_id} {'활성화' if enabled else '비활성화'}되었습니다."
FAQ_TOGGLE_NOT_FOUND = "❌ 해당 FAQ가 없습니다."

CATEGORY_CHANGE_PROMPT = "📂 새 카테고리를 선택해 주세요. (새 토픽이 생성됩니다)"

CATEGORY_PROMPT = {
    "general": "💬 무엇이든 편하게 문의해 주세요.",
    "repl": "👟 크림(KREAM) 앱에서 원하시는 상품을 찾아 화면 캡처 이미지를 보내주세요.",
    "account": "🔑 원하시는 <b>국가</b>와 <b>연식(가입 연도)</b>를 알려주세요.\n예) 미국, 2023년",
    "telf": "📱 원하시는 이용 기간을 선택해 주세요.",
}

TELF_SELECTED = "📱 <b>{duration}</b> 텔프 이용권을 선택하셨습니다.\n담당자가 곧 연락드립니다."
