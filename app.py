import streamlit as st
import yfinance as yf
import pandas as pd
import random
import time
import textwrap  # 核心修复工具
from datetime import datetime, timedelta

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="能源·周易量化",
    page_icon="☯️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. 注入 CSS 样式 (修复输入框与显示) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&family=Noto+Serif+SC:wght@500;700&family=JetBrains+Mono:wght@400;700&display=swap');

    /* 全局背景 */
    .stApp {
        background-color: #f8fafc;
    }
    
    /* 强制修复输入框颜色 (白底黑字，清晰可见) */
    .stTextInput input {
        background-color: #ffffff !important;
        color: #1e293b !important; /* 深灰色字体 */
        border: 2px solid #e2e8f0 !important;
        border-radius: 10px !important;
        padding: 10px !important;
        font-weight: bold !important;
    }
    
    /* 字体定义 */
    .tech-font { font-family: 'JetBrains Mono', monospace; }
    .trad-font { font-family: 'Noto Serif SC', serif; }
    .calligraphy { font-family: 'Ma Shan Zheng', cursive; }
    
    /* CSS 绘制卦象 (解决手机不显示问题) */
    .hex-container {
        display: flex;
        flex-direction: column-reverse; /* 从下往上画 */
        gap: 5px;
        width: 80px;
        margin: 0 auto;
    }
    .line-yang {
        width: 100%;
        height: 12px;
        background-color: #b91c1c; /* 朱砂红 */
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(185, 28, 28, 0.2);
    }
    .line-yin {
        display: flex;
        justify-content: space-between;
        width: 100%;
        height: 12px;
    }
    .line-yin-part {
        width: 42%;
        height: 100%;
        background-color: #1f2937; /* 墨色 */
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(31, 41, 55, 0.2);
    }
    
    /* 结果卡片样式 */
    .result-card {
        background: white;
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
        border: 1px solid #e2e8f0;
        text-align: center;
        margin-bottom: 20px;
    }
    
    /* 隐藏 Streamlit 自带干扰元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. 核心数据字典 (全量) ---
HEXAGRAMS = {
    "1,1,1,1,1,1": {"name": "乾", "judgment": "元亨利贞。", "interp": "【大象】天行健，君子以自强不息。<br>【量化】多头强势，动能充沛，如飞龙在天。<br>【策略】顺势做多，但需警惕高位滞涨。<br>【生活】运势极佳，适合大展宏图，忌骄傲。", "outlook": "bullish"},
    "0,0,0,0,0,0": {"name": "坤", "judgment": "元亨，利牝马之贞。", "interp": "【大象】地势坤，君子以厚德载物。<br>【量化】空头主导或底部盘整，波动率低。<br>【策略】不宜追高，适合定投或空仓观望。<br>【生活】包容忍耐，以静制动。", "outlook": "bearish"},
    "1,0,0,0,1,0": {"name": "屯", "judgment": "元亨利贞。", "interp": "【大象】云雷屯。<br>【量化】筑底阶段，震荡剧烈，方向未明。<br>【策略】建仓需谨慎，控制仓位。<br>【生活】万事开头难，积蓄力量。", "outlook": "neutral"},
    "0,1,0,0,0,1": {"name": "蒙", "judgment": "亨。", "interp": "【大象】山下出泉，蒙。<br>【量化】信息混沌，趋势不明，迷雾重重。<br>【策略】多看少动，等待信号。<br>【生活】局势不明朗，建议多咨询专家。", "outlook": "neutral"},
    "1,1,1,0,1,0": {"name": "需", "judgment": "有孚，光亨。", "interp": "【大象】云上于天，需。<br>【量化】上涨趋势中的回调，需求在积蓄。<br>【策略】逢低吸纳，持仓待涨。<br>【生活】时机未到，耐心等待。", "outlook": "bullish"},
    "0,1,0,1,1,1": {"name": "讼", "judgment": "有孚，窒惕。", "interp": "【大象】天与水违，讼。<br>【量化】多空分歧巨大，成交量放大但滞涨。<br>【策略】风险较高，建议减仓。<br>【生活】易生口角，以和为贵。", "outlook": "neutral"},
    "0,1,0,0,0,0": {"name": "师", "judgment": "贞，丈人吉。", "interp": "【大象】地中有水，师。<br>【量化】空头排列，趋势性下跌，力量集中。<br>【策略】顺势做空，严守纪律。<br>【生活】需要严明的纪律和领导。", "outlook": "bearish"},
    "0,0,0,0,1,0": {"name": "比", "judgment": "吉。", "interp": "【大象】地上有水，比。<br>【量化】板块轮动良好，市场情绪和谐。<br>【策略】跟随龙头，寻找补涨机会。<br>【生活】人际关系和谐，有贵人相助。", "outlook": "neutral"},
    "1,1,1,0,1,1": {"name": "小畜", "judgment": "亨。密云不雨。", "interp": "【大象】风行天上，小畜。<br>【量化】上涨遇阻，窄幅震荡，蓄势待发。<br>【策略】高抛低吸，短期盘整。<br>【生活】积蓄力量，不可急于求成。", "outlook": "bullish"},
    "1,1,0,1,1,1": {"name": "履", "judgment": "履虎尾。", "interp": "【大象】上天下泽，履。<br>【量化】高位震荡，风险积聚，如履薄冰。<br>【策略】设置止损，步步为营。<br>【生活】有惊无险，但须小心。", "outlook": "neutral"},
    "1,1,1,0,0,0": {"name": "泰", "judgment": "小往大来。", "interp": "【大象】天地交，泰。<br>【量化】多头市场，量价齐升，极为顺畅。<br>【策略】积极做多，享受泡沫。<br>【生活】三阳开泰，非常吉利。", "outlook": "bullish"},
    "0,0,0,1,1,1": {"name": "否", "judgment": "否之匪人。", "interp": "【大象】天地不交，否。<br>【量化】流动性枯竭，阴跌不止。<br>【策略】清仓离场，现金为王。<br>【生活】闭塞不通，宜退守。", "outlook": "bearish"},
    "1,0,1,1,1,1": {"name": "同人", "judgment": "同人于野。", "interp": "【大象】天与火，同人。<br>【量化】市场共识形成，普涨行情。<br>【策略】重仓出击，跟随主流。<br>【生活】志同道合，利于团队。", "outlook": "bullish"},
    "1,1,1,1,0,1": {"name": "大有", "judgment": "元亨。", "interp": "【大象】火在天上，大有。<br>【量化】牛市主升浪，收获颇丰。<br>【策略】持有核心资产，防止获利回吐。<br>【生活】运势昌隆，忌满招损。", "outlook": "bullish"},
    "0,0,1,0,0,0": {"name": "谦", "judgment": "君子有终。", "interp": "【大象】地中有山，谦。<br>【量化】价值低估，底部夯实。<br>【策略】逢低布局，长线持有。<br>【生活】谦虚受益，低调行事。", "outlook": "neutral"},
    "0,0,0,1,0,0": {"name": "豫", "judgment": "利建侯行师。", "interp": "【大象】雷出地奋，豫。<br>【量化】突破盘整，放量上行。<br>【策略】积极参与，顺势加仓。<br>【生活】安乐愉悦，利于行动。", "outlook": "neutral"},
    "1,0,0,1,1,0": {"name": "随", "judgment": "元亨利贞。", "interp": "【大象】泽中有雷，随。<br>【量化】趋势跟随，无明显主见。<br>【策略】右侧交易，不摸顶底。<br>【生活】随遇而安，随时变通。", "outlook": "neutral"},
    "0,1,1,0,0,1": {"name": "蛊", "judgment": "元亨。", "interp": "【大象】山下有风，蛊。<br>【量化】利空出尽，估值修复。<br>【策略】关注困境反转股。<br>【生活】整顿积弊，改革良机。", "outlook": "neutral"},
    "1,1,0,0,0,0": {"name": "临", "judgment": "元亨利贞。", "interp": "【大象】泽上有地，临。<br>【量化】多头逼空，阳线连发。<br>【策略】果断进场，持有待涨。<br>【生活】居高临下，运势增长。", "outlook": "bullish"},
    "0,0,0,0,1,1": {"name": "观", "judgment": "盥而不荐。", "interp": "【大象】风行地上，观。<br>【量化】高位滞涨，缩量整理。<br>【策略】多看少动，观察盘面。<br>【生活】冷静观察，静观其变。", "outlook": "neutral"},
    "1,0,0,1,0,1": {"name": "噬嗑", "judgment": "利用狱。", "interp": "【大象】雷电，噬嗑。<br>【量化】关键阻力位，多空激烈博弈。<br>【策略】需要放量突破，否则回落。<br>【生活】遇到阻碍，需果断解决。", "outlook": "neutral"},
    "1,0,1,0,0,1": {"name": "贲", "judgment": "小利有攸往。", "interp": "【大象】山下有火，贲。<br>【量化】题材炒作，概念火热但无支撑。<br>【策略】短线快进快出。<br>【生活】表面繁荣，需看清本质。", "outlook": "neutral"},
    "0,0,0,0,0,1": {"name": "剥", "judgment": "不利有攸往。", "interp": "【大象】山附于地，剥。<br>【量化】高位崩塌，获利盘出逃。<br>【策略】止损离场，不可抄底。<br>【生活】基础不稳，防范损失。", "outlook": "bearish"},
    "1,0,0,0,0,0": {"name": "复", "judgment": "亨。", "interp": "【大象】雷在地中，复。<br>【量化】超跌反弹，V型反转。<br>【策略】左侧建仓，长线布局。<br>【生活】一阳来复，否极泰来。", "outlook": "bullish"},
    "1,0,0,1,1,1": {"name": "无妄", "judgment": "元亨利贞。", "interp": "【大象】天下雷行，物与无妄。<br>【量化】回归价值，去除泡沫。<br>【策略】不追题材，关注基本面。<br>【生活】真实无妄，不可投机。", "outlook": "neutral"},
    "1,1,1,0,0,1": {"name": "大畜", "judgment": "利贞。", "interp": "【大象】天在山中，大畜。<br>【量化】横盘吸筹，主力建仓。<br>【策略】耐心持股，等待主升浪。<br>【生活】积蓄巨大，厚积薄发。", "outlook": "neutral"},
    "1,0,0,0,0,1": {"name": "颐", "judgment": "贞吉。", "interp": "【大象】山下有雷，颐。<br>【量化】缩量整固，上下两难。<br>【策略】高抛低吸，或休息观望。<br>【生活】颐养身心，此时宜静。", "outlook": "neutral"},
    "0,1,1,1,1,0": {"name": "大过", "judgment": "栋桡。", "interp": "【大象】泽灭木，大过。<br>【量化】严重超买，乖离率过大。<br>【策略】风险极大，建议清仓。<br>【生活】压力过大，需释放压力。", "outlook": "neutral"},
    "0,1,0,0,1,0": {"name": "坎", "judgment": "习坎。", "interp": "【大象】水流而不盈，习坎。<br>【量化】破位下行，深不见底。<br>【策略】现金为王，切勿接飞刀。<br>【生活】重重险陷，务必保守。", "outlook": "bearish"},
    "1,0,1,1,0,1": {"name": "离", "judgment": "利贞。", "interp": "【大象】明两作，离。<br>【量化】加速赶顶，情绪狂热。<br>【策略】短线博弈，快进快出。<br>【生活】如日中天，但来去匆匆。", "outlook": "bullish"},
    "0,0,1,1,1,0": {"name": "咸", "judgment": "亨。", "interp": "【大象】山上有泽，咸。<br>【量化】消息刺激，脉冲式行情。<br>【策略】关注消息面，灵活操作。<br>【生活】感应沟通，利于社交。", "outlook": "neutral"},
    "0,1,1,1,0,0": {"name": "恒", "judgment": "亨。", "interp": "【大象】雷风，恒。<br>【量化】趋势稳定，慢牛或阴跌。<br>【策略】顺着当前趋势操作。<br>【生活】恒久持续，保持现状。", "outlook": "neutral"},
    "0,0,1,1,1,1": {"name": "遁", "judgment": "亨，小利贞。", "interp": "【大象】天下有山，遁。<br>【量化】诱多出货，重心下移。<br>【策略】逢反弹减仓，避险为主。<br>【生活】退避隐遁，不宜争锋。", "outlook": "bearish"},
    "1,1,1,1,0,0": {"name": "大壮", "judgment": "利贞。", "interp": "【大象】雷在天上，大壮。<br>【量化】放量突破，强势上攻。<br>【策略】重仓持有，防冲高回落。<br>【生活】声势壮大，适合进攻。", "outlook": "bullish"},
    "0,0,0,1,0,1": {"name": "晋", "judgment": "康侯用锡马。", "interp": "【大象】明出地上，晋。<br>【量化】稳步推升，进二退一。<br>【策略】积极进取，持股待涨。<br>【生活】旭日东升，步步高升。", "outlook": "bullish"},
    "1,0,1,0,0,0": {"name": "明夷", "judgment": "利艰贞。", "interp": "【大象】明入地中，明夷。<br>【量化】黑天鹅事件，大幅跳水。<br>【策略】空仓避险，不要抱有幻想，韬光养晦。<br>【生活】前景黯淡，需忍耐。", "outlook": "bearish"},
    "1,0,1,0,1,1": {"name": "家人", "judgment": "利女贞。", "interp": "【大象】风自火出，家人。<br>【量化】防御性板块走强，结构性行情。<br>【策略】关注消费、公用事业。<br>【生活】相亲相爱，基础稳固。", "outlook": "neutral"},
    "1,1,0,1,0,1": {"name": "睽", "judgment": "小事吉。", "interp": "【大象】上火下泽，睽。<br>【量化】板块分化，赚钱效应差。<br>【策略】多空分歧大，小仓位试错，不宜重仓。<br>【生活】意见不合，小事可为。", "outlook": "neutral"},
    "0,0,1,0,1,0": {"name": "蹇", "judgment": "利西南。", "interp": "【大象】山上有水，蹇。<br>【量化】上有压力下有支撑，僵持不下。<br>【策略】不宜硬闯，等待变盘。<br>【生活】前有险阻，最好求援。", "outlook": "bearish"},
    "0,1,0,1,0,0": {"name": "解", "judgment": "利西南。", "interp": "【大象】雷雨作，解。<br>【量化】利空消化，止跌回升。<br>【策略】布局超跌反弹。<br>【生活】冰消瓦解，困难消除。", "outlook": "bullish"},
    "1,1,0,0,0,1": {"name": "损", "judgment": "有孚，元吉。", "interp": "【大象】山下有泽，损。<br>【量化】缩量阴跌，市值缩水。<br>【策略】止损换股，先失后得。<br>【生活】减损获益，需投入成本。", "outlook": "bearish"},
    "1,0,0,0,1,1": {"name": "益", "judgment": "利有攸往。", "interp": "【大象】风雷，益。<br>【量化】政策利好，资金流入。<br>【策略】积极参与，大展拳脚。<br>【生活】损上益下，环境宽松。", "outlook": "bullish"},
    "1,1,1,1,1,0": {"name": "夬", "judgment": "扬于王庭。", "interp": "【大象】泽上于天，夬。<br>【量化】冲关时刻，多头总攻。<br>【策略】必须果断跟进，切勿犹豫。<br>【生活】决断突破，必须果断。", "outlook": "bullish"},
    "0,1,1,1,1,1": {"name": "姤", "judgment": "女壮，勿用取女。", "interp": "【大象】天下有风，姤。<br>【量化】冲高回落，头部迹象。<br>【策略】虽然上涨但需减仓。<br>【生活】不期而遇，防微杜渐。", "outlook": "bearish"},
    "0,0,0,0,1,1": {"name": "萃", "judgment": "亨。", "interp": "【大象】泽上于地，萃。<br>【量化】资金抱团，龙头效应。<br>【策略】加入核心资产，享受泡沫。<br>【生活】聚集荟萃，人气高涨。", "outlook": "bullish"},
    "0,1,1,0,0,0": {"name": "升", "judgment": "元亨。", "interp": "【大象】地中生木，升。<br>【量化】稳步上涨，均线多头。<br>【策略】坚定持仓，不轻易下车。<br>【生活】积小成大，步步高升。", "outlook": "bullish"},
    "0,1,0,1,1,0": {"name": "困", "judgment": "亨，贞，大人吉。", "interp": "【大象】泽无水，困。<br>【量化】成交低迷，无人问津。<br>【策略】不要轻易抄底，效率极低。<br>【生活】困顿穷乏，需坚守。", "outlook": "neutral"},
    "0,1,1,0,1,0": {"name": "井", "judgment": "改邑不改井。", "interp": "【大象】木上有水，井。<br>【量化】织布机行情，原地踏步。<br>【策略】适合高股息策略，做定投。<br>【生活】价值仍在，适合定投。", "outlook": "neutral"},
    "1,0,1,1,1,0": {"name": "革", "judgment": "元亨利贞。", "interp": "【大象】泽中有火，革。<br>【量化】风格切换，新老交替。<br>【策略】调仓换股，跟随新热点。<br>【生活】除旧布新，面临变革。", "outlook": "neutral"},
    "0,1,1,1,0,1": {"name": "鼎", "judgment": "元吉。", "interp": "【大象】木上有火，鼎。<br>【量化】新周期确立，权重搭台，格局稳定。<br>【策略】布局蓝筹，长线看好。<br>【生活】稳重图新，新的繁荣。", "outlook": "bullish"},
    "1,0,0,1,0,0": {"name": "震", "judgment": "亨。", "interp": "【大象】洊雷，震。<br>【量化】消息面利空，盘中急跌。<br>【策略】或是黄金坑，注意情绪修复。<br>【生活】突发事件，有惊无险。", "outlook": "neutral"},
    "0,0,1,0,0,1": {"name": "艮", "judgment": "艮其背。", "interp": "【大象】兼山，艮。<br>【量化】上涨乏力，多重顶。<br>【策略】止盈离场，休息观望。<br>【生活】动静适时，止步不前。", "outlook": "neutral"},
    "0,0,1,0,1,1": {"name": "渐", "judgment": "女归吉。", "interp": "【大象】山上有木，渐。<br>【量化】碎步上行，慢牛行情。<br>【策略】保持耐心，不要被震荡洗出局。<br>【生活】循序渐进，终成大器。", "outlook": "neutral"},
    "1,1,0,1,0,0": {"name": "归妹", "judgment": "征凶。", "interp": "【大象】泽上有雷，归妹。<br>【量化】走势怪异，诱多陷阱。<br>【策略】如果不看好，坚决不参与。<br>【生活】错位之象，易失误。", "outlook": "neutral"},
    "1,0,1,1,0,0": {"name": "丰", "judgment": "亨。", "interp": "【大象】雷电皆至，丰。<br>【量化】成交天量，情绪亢奋。<br>【策略】逐步止盈，落袋为安。<br>【生活】达到顶峰，盛极必衰。", "outlook": "bullish"},
    "0,0,1,1,1,0": {"name": "旅", "judgment": "小亨。", "interp": "【大象】山上有火，旅。<br>【量化】游资主导，一日游行情。<br>【策略】打板或超短线，快进快出。<br>【生活】漂泊不定，不宜久留。", "outlook": "neutral"},
    "0,1,1,0,1,1": {"name": "巽", "judgment": "小亨。", "interp": "【大象】随风，巽。<br>【量化】市场形成一致预期，无脑跟随。<br>【策略】不要逆势操作，风往哪吹往哪倒。<br>【生活】顺风而行，顺从时势。", "outlook": "neutral"},
    "1,1,0,1,1,0": {"name": "兑", "judgment": "亨。", "interp": "【大象】丽泽，兑。<br>【量化】交易活跃，换手率高。<br>【策略】积极参与热点，但防高位被套。<br>【生活】喜悦沟通，防口舌是非。", "outlook": "bullish"},
    "0,1,0,0,1,1": {"name": "涣", "judgment": "亨。", "interp": "【大象】风行水上，涣。<br>【量化】筹码松动，主力撤退，行情散去。<br>【策略】该跑就跑，不要留恋。<br>【生活】离散之象，人心涣散，凝聚力瓦解。", "outlook": "neutral"},
    "1,1,0,0,1,0": {"name": "节", "judgment": "亨。", "interp": "【大象】泽上有水，节。<br>【量化】箱体震荡，上有顶下有底。<br>【策略】高抛低吸，懂得止盈。<br>【生活】节制适度，量力而行。", "outlook": "neutral"},
    "1,1,0,0,1,1": {"name": "中孚", "judgment": "豚鱼吉。", "interp": "【大象】泽上有风，中孚。<br>【量化】技术指标有效，走势规范。<br>【策略】按技术图形操作，相信信号。<br>【生活】诚信感通，脚下有路。", "outlook": "neutral"},
    "0,0,1,1,0,0": {"name": "小过", "judgment": "亨，利贞。", "interp": "【大象】山上有雷，小过。<br>【量化】小幅波动，大趋势不明。<br>【策略】小仓位试错，不要重仓博弈。<br>【生活】小有过度，宜守。", "outlook": "neutral"},
    "1,0,1,0,1,0": {"name": "既济", "judgment": "亨，小利贞。", "interp": "【大象】水在火上，既济。<br>【量化】完美收官，利好兑现。<br>【策略】获利了结，见好就收。<br>【生活】大功告成，防盛极而衰。", "outlook": "neutral"},
    "0,1,0,1,0,1": {"name": "未济", "judgment": "亨。", "interp": "【大象】火在水上，未济。<br>【量化】行情未完，充满变数。<br>【策略】寻找新的增长点，在此博弈。<br>【生活】未完成，充满希望。", "outlook": "neutral"}
}

# --- 4. 辅助函数: 生成卦象HTML (压扁成单行，去缩进) ---
def get_hexagram_html(key_str):
    lines = key_str.split(",") 
    html_lines = []
    # 视觉显示 Top->Bottom (上->初)，所以需要 reversed
    for val in reversed(lines):
        if val == "1":
            html_lines.append('<div class="line-yang"></div>')
        else:
            html_lines.append('<div class="line-yin"><div class="line-yin-part"></div><div class="line-yin-part"></div></div>')
    
    return f'<div class="hex-container">{"".join(html_lines)}</div>'

# --- 5. 计算逻辑 ---
def calculate_hexagram(df):
    try:
        closes = df['Close'].values.flatten()
        opens = df['Open'].values.flatten()
    except:
        closes = df['Close']
        opens = df['Open']
    
    changes = abs((closes - opens) / opens)
    avg_change = changes.mean() 
    volatility_threshold = avg_change * 1.5
    
    ben_lines = [] 
    zhi_lines = [] 
    details = []

    # 取最后6天，倒序遍历 (i=0是最新)
    # 逻辑：df.tail(6) 是 [Oldest...Newest]
    # 反转后 subset 是 [Newest...Oldest]
    subset = df.tail(6).iloc[::-1] 
    
    for i in range(6):
        row = subset.iloc[i]
        
        c = float(row['Close'])
        o = float(row['Open'])
        
        is_up = c >= o
        change_pct = abs((c - o) / o)
        
        is_moving = change_pct > volatility_threshold
        
        if is_up:
            line_val = 9 if is_moving else 7
        else:
            line_val = 6 if is_moving else 8
            
        ben_val = 1 if line_val in [7, 9] else 0
        zhi_val = 0 if line_val == 9 else (1 if line_val == 6 else ben_val)
        
        ben_lines.append(str(ben_val))
        zhi_lines.append(str(zhi_val))
        
        details.append({
            "date": row.name.strftime('%Y-%m-%d'),
            "close": c,
            "change": (c - o) / o,
            "type": line_val,
            "position": i 
        })
        
    return ",".join(ben_lines), ",".join(zhi_lines), details

# --- 6. 界面布局 ---

# TABS
tab_market, tab_daily = st.tabs(["📈 市场量化 (Tech)", "🎲 趣味问卜 (国潮)"])

# --- MARKET TAB ---
with tab_market:
    st.markdown('<div class="tech-font">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        symbol = st.selectbox("选择品种 (Asset)", 
                     ["BZ=F", "NG=F", "TTF=F", "RB=F"], 
                     format_func=lambda x: {
                         "BZ=F": "🛢️ Brent Crude", 
                         "NG=F": "🔥 Natural Gas",
                         "TTF=F": "🇪🇺 Dutch TTF", 
                         "RB=F": "⛽ RBOB Gasoline"
                     }[x])
    with col2:
        date_val = st.date_input("基准日期 (Date)", datetime.now())
        
    if st.button("🚀 启动量化模型 (RUN MODEL)", type="primary"):
        with st.spinner("Connecting to Exchange..."):
            try:
                end_date = pd.to_datetime(date_val)
                start_date = end_date - timedelta(days=40)
                
                df = yf.download(symbol, start=start_date, end=end_date + timedelta(days=1), progress=False)
                
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                if len(df) < 6:
                    st.error("数据不足，无法生成卦象 (需至少6个交易日)")
                else:
                    ben_key, zhi_key, line_details = calculate_hexagram(df)
                    
                    ben_info = HEXAGRAMS.get(ben_key)
                    zhi_info = HEXAGRAMS.get(zhi_key)
                    
                    if not ben_info:
                        st.error(f"System Error: Invalid Hexagram Key {ben_key}")
                    else:
                        st.markdown("---")
                        
                        c1, c2 = st.columns(2)
                        
                        # 1. 本卦卡片 (修复缩进问题)
                        with c1:
                            hex_html = get_hexagram_html(ben_key)
                            # 预处理解释文本，去除潜在的换行符
                            interp_clean = ben_info['interp'].replace('\n', '')
                            
                            html_str = textwrap.dedent(f"""
                                <div class="result-card">
                                    <div style="color:#64748b; font-weight:bold; font-size:12px; margin-bottom:5px;">CURRENT PHASE (本卦)</div>
                                    {hex_html}
                                    <div style="font-size:24px; font-weight:bold; margin-top:10px;">{ben_info['name']}</div>
                                    <div style="font-size:14px; font-style:italic; color:#64748b;">{ben_info['judgment']}</div>
                                    <hr style="margin:10px 0; border-top: 1px solid #e2e8f0;">
                                    <div style="text-align:left; font-size:13px; line-height:1.6;">
                                        {interp_clean}
                                    </div>
                                </div>
                            """).strip()
                            st.markdown(html_str, unsafe_allow_html=True)
                            
                        # 2. 之卦卡片 (修复缩进问题)
                        with c2:
                            hex_html_zhi = get_hexagram_html(zhi_key)
                            opacity = "1" if ben_key != zhi_key else "0.5"
                            suffix = "(变卦)" if ben_key != zhi_key else "(无变动)"
                            interp_clean_zhi = zhi_info['interp'].replace('\n', '')
                            
                            html_str_zhi = textwrap.dedent(f"""
                                <div class="result-card" style="opacity:{opacity};">
                                    <div style="color:#64748b; font-weight:bold; font-size:12px; margin-bottom:5px;">PROJECTION (之卦)</div>
                                    {hex_html_zhi}
                                    <div style="font-size:24px; font-weight:bold; margin-top:10px;">{zhi_info['name']} {suffix}</div>
                                    <div style="font-size:14px; font-style:italic; color:#64748b;">{zhi_info['judgment']}</div>
                                    <hr style="margin:10px 0; border-top: 1px solid #e2e8f0;">
                                    <div style="text-align:left; font-size:13px; line-height:1.6;">
                                        {interp_clean_zhi}
                                    </div>
                                </div>
                            """).strip()
                            st.markdown(html_str_zhi, unsafe_allow_html=True)

                        st.subheader("📊 K-Line Sequence")
                        
                        table_data = []
                        pos_map = ["初爻 (Bottom)", "二爻", "三爻", "四爻", "五爻", "上爻 (Top)"]
                        
                        for d in line_details:
                            type_str = "阳 (7)"
                            if d['type'] == 8: type_str = "阴 (8)"
                            if d['type'] == 9: type_str = "老阳 (9) 🔴"
                            if d['type'] == 6: type_str = "老阴 (6) 🔵"
                            
                            table_data.append({
                                "Date": d['date'],
                                "Pos": pos_map[d['position']],
                                "Close": f"{d['close']:.2f}",
                                "Chg%": f"{d['change']*100:.2f}%",
                                "Type": type_str
                            })
                        
                        st.dataframe(pd.DataFrame(table_data), use_container_width=True)

            except Exception as e:
                st.error(f"Data Error: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# --- DAILY TAB ---
with tab_daily:
    st.markdown('<div class="trad-font">', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align:center; padding: 30px 0;">
        <h1 class="calligraphy" style="font-size: 42px; color: #b91c1c;">诚心问卜</h1>
        <p style="color: #888; font-size: 14px;">默念心中之事，点击下方按钮起卦</p>
    </div>
    """, unsafe_allow_html=True)
    
    question = st.text_input("", placeholder="在此输入您的问题...", key="q_input")
    
    if st.button("🎲 掷出六爻 (SHAKE)", type="secondary", use_container_width=True):
        if not question:
            st.warning("请先输入问题")
        else:
            with st.spinner("正在以此诚心，沟通天地..."):
                time.sleep(1.5)
                
                lines = []
                for _ in range(6):
                    c1 = 3 if random.random() > 0.5 else 2
                    c2 = 3 if random.random() > 0.5 else 2
                    c3 = 3 if random.random() > 0.5 else 2
                    lines.append(c1 + c2 + c3)
                
                ben_res = []
                zhi_res = []
                for val in lines:
                    if val in [7, 9]: 
                        ben_res.append("1")
                        zhi_res.append("0" if val == 9 else "1")
                    else: 
                        ben_res.append("0")
                        zhi_res.append("1" if val == 6 else "0")
                
                d_ben_key = ",".join(ben_res)
                d_zhi_key = ",".join(zhi_res)
                
                d_ben = HEXAGRAMS[d_ben_key]
                d_zhi = HEXAGRAMS[d_zhi_key]
                
                ben_html = get_hexagram_html(d_ben_key)
                zhi_html = get_hexagram_html(d_zhi_key)
                
                # Daily Result Card (修复缩进问题)
                daily_interp_clean = d_ben['interp'].replace('\n', '')
                
                daily_html = textwrap.dedent(f"""
                <div class="result-card" style="background-color:#fffbf0; border:2px solid #b91c1c; padding:20px;">
                    <div style="text-align:center; margin-bottom:20px; color:#b91c1c; font-weight:bold; font-size:18px;">问：{question}</div>
                    
                    <div style="display:flex; justify-content:space-around; align-items:flex-start;">
                        <div style="text-align:center; flex:1;">
                            <div style="font-size:12px; color:#888; margin-bottom:8px;">本卦 (现状)</div>
                            {ben_html}
                            <div class="calligraphy" style="font-size:32px; margin-top:8px; color:#333;">{d_ben['name']}</div>
                            <div style="font-size:13px; color:#666;">{d_ben['judgment']}</div>
                        </div>
                        
                        <div style="text-align:center; flex:1; opacity: {1.0 if d_ben_key != d_zhi_key else 0.3};">
                            <div style="font-size:12px; color:#888; margin-bottom:8px;">之卦 (变数)</div>
                            {zhi_html}
                            <div class="calligraphy" style="font-size:32px; margin-top:8px; color:#333;">{d_zhi['name']}</div>
                            <div style="font-size:13px; color:#666;">{d_zhi['judgment']}</div>
                        </div>
                    </div>
                    
                    <hr style="border-color:#e5e7eb; margin:20px 0;">
                    
                    <div style="background:rgba(255,255,255,0.6); padding:15px; border-radius:8px; border:1px dashed #d1d5db;">
                        <p style="font-weight:bold; color:#b91c1c; margin-bottom:5px;">💡 锦囊妙计：</p>
                        <div style="line-height:1.6; font-size:14px; color:#333;">
                            {daily_interp_clean}
                        </div>
                        {f'<div style="margin-top:10px; font-size:13px; color:#d97706;">⚡ <strong>变爻启示：</strong>局势正在向 {d_zhi["name"]} 转变，请参考之卦建议。</div>' if d_ben_key != d_zhi_key else ''}
                    </div>
                </div>
                """).strip()
                
                st.markdown(daily_html, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)