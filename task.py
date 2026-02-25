## Importing libraries and files
from crewai import Task

from agents import financial_analyst, verifier, investment_advisor, risk_assessor
from tools import FinancialDocumentTool

## Creating a task to analyze the financial document
analyze_financial_document = Task(
    description="""Conduct a comprehensive analysis of the financial document to address the user's query: {query}
    
    Analysis steps:
    1. Thoroughly read and parse the financial document
    2. Extract key financial metrics (revenue, profit, margins, cash flow, debt, assets, etc.)
    3. Identify trends and patterns in the financial data
    4. Assess the company's financial health and performance
    5. Highlight strengths and areas of concern
    6. Address the specific query with evidence from the document
    
    Base all conclusions on actual data from the document. Cite specific numbers and metrics.
    Avoid speculation - only state what can be supported by the document.""",

    expected_output="""A detailed financial analysis report with:
    - Executive summary addressing the query
    - Key financial metrics extracted from the document with actual values
    - Analysis of financial performance (revenue growth, profitability, efficiency)
    - Cash flow and liquidity assessment
    - Debt and capital structure evaluation
    - Trend analysis (if multi-period data available)
    - Key strengths identified
    - Areas of concern or risk factors
    - Specific data points supporting each conclusion
    
    Format: Well-structured with clear sections, bullet points for key findings.""",

    agent=financial_analyst,
    tools=[FinancialDocumentTool.read_data_tool],
    async_execution=False,
    context=[verification],
)

## Creating an investment analysis task
investment_analysis = Task(
    description="""Based on the financial analysis, provide investment recommendations and insights.
    
    Analysis steps:
    1. Review the financial analysis findings
    2. Evaluate investment attractiveness based on fundamentals
    3. Consider valuation metrics and growth potential
    4. Assess competitive position and market opportunities
    5. Identify key drivers and catalysts
    6. Address user's specific query: {query}
    
    Provide balanced, evidence-based investment insights. Consider different investor profiles
    (conservative, moderate, aggressive). Include appropriate disclaimers.""",

    expected_output="""Investment analysis report including:
    - Investment thesis summary (bull and bear cases)
    - Key investment highlights from financial data
    - Valuation assessment (is it overvalued, fairly valued, undervalued based on metrics)
    - Growth potential and drivers
    - Competitive strengths and advantages
    - Recommendations for different risk profiles:
      * Conservative investors
      * Moderate risk investors  
      * Aggressive/growth investors
    - Key metrics to monitor
    - Important considerations and caveats
    - Standard disclaimer about investment risks and the need for personal due diligence
    
    Base all recommendations on the financial data analyzed, not speculation.""",

    agent=investment_advisor,
    tools=[FinancialDocumentTool.read_data_tool],
    async_execution=False,
    context=[verification, analyze_financial_document],
)

## Creating a risk assessment task
risk_assessment = Task(
    description="""Conduct a comprehensive risk assessment based on the financial document analysis.
    
    User query: {query}
    
    Analysis steps:
    1. Identify and categorize risks from the financial data:
       - Financial risks (debt levels, liquidity, cash flow stability)
       - Operational risks (cost structure, efficiency)
       - Market risks (industry trends, competition, economic sensitivity)
       - Company-specific risks
    2. Assess the severity and likelihood of each risk
    3. Evaluate risk mitigation measures already in place
    4. Provide risk management recommendations
    
    Use established risk assessment frameworks. Base analysis on actual data from
    the financial document.""",

    expected_output="""Comprehensive risk assessment report:
    
    1. Executive Risk Summary
       - Overall risk level (Low/Moderate/High) with justification
       - Top 3-5 critical risks
    
    2. Detailed Risk Analysis:
       - Financial Risks:
         * Leverage/debt risk (debt ratios, interest coverage)
         * Liquidity risk (current ratio, cash position)
         * Cash flow stability
       - Operational Risks:
         * Cost structure and margin pressure
         * Operational efficiency concerns
       - Market/Industry Risks:
         * Competitive position
         * Market dynamics and trends
         * Economic sensitivity
       - Other Material Risks
    
    3. Risk Metrics:
       - Key risk indicators from the financial data
       - Comparison to industry benchmarks (if available)
    
    4. Risk Mitigation:
       - Existing risk controls identified
       - Recommended risk management strategies:
         * Diversification approaches
         * Hedging considerations
         * Position sizing guidelines
       - Portfolio construction suggestions
    
    5. Risk Monitoring:
       - Key metrics to track
       - Warning signs to watch for
    
    All risk assessments must be evidence-based and tied to specific financial data.""",

    agent=risk_assessor,
    tools=[FinancialDocumentTool.read_data_tool],
    async_execution=False,
    context=[verification, analyze_financial_document, investment_analysis],
)

## Document verification task - runs first
verification = Task(
    description="""Verify that the uploaded document is a legitimate financial document.
    
    Analysis steps:
    1. Examine the document structure and content
    2. Check for standard financial document elements (financial statements, metrics, reports)
    3. Verify presence of financial terminology and numerical data
    4. Assess data completeness and quality
    5. Determine if document contains sufficient information for meaningful analysis
    
    Provide a clear validation result stating whether this is a valid financial document
    and identify any issues or missing information.""",

    expected_output="""A structured verification report including:
    - Document type identification (e.g., annual report, quarterly earnings, financial statement)
    - Validation status (Valid/Invalid) with clear reasoning
    - List of financial elements found (balance sheet, income statement, cash flow, etc.)
    - Data quality assessment
    - Any concerns or missing critical information
    - Recommendation on whether to proceed with full analysis""",

    agent=verifier,
    tools=[FinancialDocumentTool.read_data_tool],
    async_execution=False,
)
    async_execution=False
)