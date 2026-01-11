"""
Custom CSS styling for AI-Onboarder
Clean, minimal, professional design
"""

def get_custom_css():
    """Return custom CSS for clean UI"""
    return """
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background-color: #f8fafc;
    }
    
    /* Main Title Styling */
    h1 {
        color: #0f172a !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }
    
    /* Subheader Styling */
    h2, h3 {
        color: #1e293b !important;
        font-weight: 600 !important;
    }
    
    /* Chat Container - Full height like ChatGPT */
    .chat-container {
        display: flex;
        flex-direction: column;
        height: calc(100vh - 200px);
        max-height: 800px;
        overflow-y: auto;
    }
    
    /* Chat Messages Area - Scrollable with smooth scroll */
    .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 20px;
        margin-bottom: 80px;
        scroll-behavior: smooth;
    }
    
    /* Chat Input - Sticky at bottom */
    [data-testid="stChatInput"] {
        position: sticky;
        bottom: 0;
        background: white;
        padding: 16px 0;
        border-top: 1px solid #e2e8f0;
        z-index: 100;
    }
    
    /* Example Question Buttons */
    .stButton button[kind="secondary"] {
        background: white !important;
        border: 1px solid #e2e8f0 !important;
        color: #475569 !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton button[kind="secondary"]:hover {
        border-color: #3b82f6 !important;
        color: #3b82f6 !important;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1) !important;
    }
    
    /* User Message - Left Side */
    [data-testid="stChatMessage"][data-testid*="user"] {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 12px 16px;
        margin: 8px 0 8px auto;
        max-width: 70%;
        text-align: left;
    }
    
    /* Assistant Message - Right Side */
    [data-testid="stChatMessage"][data-testid*="assistant"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 12px 16px;
        margin: 8px auto 8px 0;
        max-width: 70%;
        text-align: left;
    }
    
    /* Chat Input Container - Sticky at Bottom */
    [data-testid="stChatInput"] {
        position: sticky;
        bottom: 0;
        background: white;
        padding: 16px 0;
        border-top: 1px solid #e2e8f0;
        z-index: 100;
    }
    
    /* Chat Input */
    .stChatInput {
        border-radius: 8px !important;
        border: 2px solid #e2e8f0 !important;
        padding: 12px 16px !important;
        transition: border-color 0.2s ease;
    }
    
    .stChatInput:focus {
        border-color: #3b82f6 !important;
        outline: none !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: #3b82f6;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 500;
        font-size: 14px;
        transition: all 0.2s ease;
        border: 1px solid transparent;
    }
    
    .stButton > button:hover {
        background: #2563eb;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
    }
    
    /* Primary Button */
    .stButton > button[kind="primary"] {
        background: #3b82f6;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: #2563eb;
    }
    
    /* Secondary Button */
    .stButton > button[kind="secondary"] {
        background: white;
        color: #475569;
        border: 1px solid #e2e8f0;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: #f8fafc;
        border-color: #cbd5e1;
    }
    
    /* Cards */
    .project-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        border: 1px solid #e2e8f0;
        transition: all 0.2s ease;
    }
    
    .project-card:hover {
        border-color: #cbd5e1;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: white;
        border-bottom: 1px solid #e2e8f0;
        padding: 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 0;
        padding: 12px 20px;
        font-weight: 500;
        color: #64748b;
        border-bottom: 2px solid transparent;
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #3b82f6;
        background: #f8fafc;
    }
    
    .stTabs [aria-selected="true"] {
        background: white;
        color: #3b82f6 !important;
        border-bottom: 2px solid #3b82f6;
    }
    
    /* Info/Warning/Success Boxes */
    .stAlert {
        border-radius: 8px;
        border-left: 3px solid;
        padding: 12px 16px;
        animation: slideIn 0.2s ease-out;
    }
    
    /* Success Box */
    [data-testid="stNotificationContentSuccess"] {
        background: #f0fdf4;
        border-left-color: #10b981;
        color: #065f46;
    }
    
    /* Info Box */
    [data-testid="stNotificationContentInfo"] {
        background: #eff6ff;
        border-left-color: #3b82f6;
        color: #1e40af;
    }
    
    /* Warning Box */
    [data-testid="stNotificationContentWarning"] {
        background: #fffbeb;
        border-left-color: #f59e0b;
        color: #92400e;
    }
    
    /* Error Box */
    [data-testid="stNotificationContentError"] {
        background: #fef2f2;
        border-left-color: #ef4444;
        color: #991b1b;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px 16px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: #f8fafc;
        border-color: #cbd5e1;
    }
    
    /* Select Box */
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
    
    /* Text Input */
    .stTextInput > div > div {
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        transition: border-color 0.2s ease;
    }
    
    .stTextInput > div > div:focus-within {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #3b82f6 !important;
    }
    
    /* Metric */
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
        color: #0f172a;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: white;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Code Blocks */
    .stCodeBlock {
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }
    
    /* Welcome Card */
    .welcome-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 32px;
        margin-bottom: 24px;
        text-align: center;
    }
    
    /* Feature Card */
    .feature-card {
        background: white;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        border: 1px solid #e2e8f0;
        transition: all 0.2s ease;
    }
    
    .feature-card:hover {
        border-color: #cbd5e1;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    
    /* Status Badge */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: 500;
        font-size: 12px;
        margin: 4px;
    }
    
    .status-pending {
        background: #fef3c7;
        color: #92400e;
    }
    
    .status-ready {
        background: #d1fae5;
        color: #065f46;
    }
    
    .status-generating {
        background: #dbeafe;
        color: #1e40af;
    }
    
    .status-error {
        background: #fee2e2;
        color: #991b1b;
    }
    
    /* Chat Welcome Message */
    .chat-welcome {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        text-align: center;
    }
    
    /* Example Questions */
    .example-question {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 10px 14px;
        margin: 6px 0;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 14px;
        text-align: left;
    }
    
    .example-question:hover {
        border-color: #3b82f6;
        background: #f8fafc;
    }
    
    /* Hero Section */
    .hero-section {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 40px;
        margin-bottom: 32px;
        text-align: center;
    }
    
    /* Divider */
    hr {
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 24px 0;
    }
    </style>
    """
