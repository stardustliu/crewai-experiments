import praw
import time
import os

from langchain.tools import tool
from langchain.llms import Ollama
from crewai import Agent, Task, Process, Crew

from langchain.agents import load_tools
from groq import Groq
from openai import OpenAI

#加载human参与循环
human_tools = load_tools(["human"])

# 加载gpt4的api key
#api = os.environ.get("OPENAI_API_KEY")

# 通过Ollama使用本地模型
#mistral = Ollama(model="mistral")

#groq_client = OpenAI(
#    #api_key = os.environ.get("GROQ_API_KEY"),
#    api_key = "sk-4tXCPaKykcp9n1oeZ2JZUtg88LOkoxyamazEtfp8PP42d5cw",
#    base_url = "https://api.moonshot.cn/v1",
#    #model = "llama2-70b-4096",
#)

os.environ["OPENAI_MODEL_NAME"]="gpt-3.5-turbo-0125"
#os.environ["OPENAI_MODEL_NAME"]="moonshot-v1-8k"

#OPENAI_API_KEY="sk-4tXCPaKykcp9n1oeZ2JZUtg88LOkoxyamazEtfp8PP42d5cw"
#OPENAI_API_BASE="https://api.moonshot.cn/v1"
#OPENAI_MODEL_NAME="moonshot-v1-8k"


class BrowserTool:
    @tool("Scrape reddit content")
    def scrape_reddit(max_comments_per_post=7):
        """Useful to scrape a reddit content"""
        reddit = praw.Reddit(
            client_id="2v3pe84Oh5l-gunXUifPgg",
            client_secret="0C1wLwkZxE3ygGlGhcY8LALh4461wQ",
            user_agent="lg_news_bot",
        )
        # 定位到LocalLLama 频道
        subreddit = reddit.subreddit("LocalLLaMA")
        scraped_data = []

        for post in subreddit.hot(limit=12):
            post_data = {"title": post.title, "url": post.url, "comments": []}

            try:
                post.comments.replace_more(limit=0)  # Load top-level comments only
                comments = post.comments.list()
                if max_comments_per_post is not None:
                    comments = comments[:7]

                for comment in comments:
                    post_data["comments"].append(comment.body)

                scraped_data.append(post_data)

            except praw.exceptions.APIException as e:
                print(f"API Exception: {e}")
                time.sleep(60)  # Sleep for 1 minute before retrying

        return scraped_data


"""
- 定义研究最新人工智能工具并撰写博客的agents
- explorer 将使用互联网和LocalLLama subreddit来获取所有最新消息
- writer 将撰写草稿
- critique 将提供反馈，并确保博客文本引人入胜且易于理解
"""

# explorer agent 定义
explorer = Agent(
    role="Senior Researcher",
    # 目标：在 2024 年，在 LocalLLama 子论坛上找到并探索最令人兴奋的项目和公司
    goal="Find and explore the most exciting projects and companies on LocalLLama subreddit in 2024",
    # 你是一位优秀的策略专家，擅长发现人工智能、技术和机器学习领域的新兴趋势和公司。您擅长在LocalLLama专栏中找到有趣、令人兴奋的项目。
    # 你将抓取的数据转化为详细报告，报告中列出了人工智能/机器学习领域中最令人兴奋的项目和公司的名称。请仅使用来自LocalLLama专栏的抓取数据进行报告。
    backstory="""You are and Expert strategist that knows how to spot emerging trends and companies in AI, tech and machine learning. 
    You're great at finding interesting, exciting projects on LocalLLama subreddit. You turned scraped data into detailed reports with names
    of most exciting projects an companies in the ai/ml world. ONLY use scraped data from LocalLLama subreddit for the report. Answer in Chinese
    """,
    verbose=True,
    allow_delegation=False,
    tools=[BrowserTool().scrape_reddit] + human_tools,
    #llm=mistral,  # remove to use default gpt-4
    #llm=groq_client,
)

# writer agent 定义
writer = Agent(
    role="Senior Technical Writer",
    # 用简单易懂的词汇撰写关于最新AI项目的引人入胜和有趣的博客文章
    goal="Write engaging and interesting blog post about latest AI projects using simple, layman vocabulary",
    # 您是一位在技术创新领域，尤其是人工智能和机器学习领域的专业作家。您知道如何以引人入胜、有趣但简单、直接且简洁的方式进行写作。
    # 您知道如何通过使用通俗易懂的词语，将复杂的技术术语以有趣的方式呈现给普通观众。只使用来自LocalLLaMA subreddit的抓取数据来撰写博客
    backstory="""You are an Expert Writer on technical innovation, especially in the field of AI and machine learning. You know how to write in 
    engaging, interesting but simple, straightforward and concise. You know how to present complicated technical terms to general audience in a 
    fun way by using layman words.ONLY use scraped data from LocalLLama subreddit for the blog. Answer in Chinese""",
    verbose=True,
    allow_delegation=True,
    #llm=mistral,  # remove to use default gpt-4
    #llm=groq_client,
)

# critique agent 定义
critic = Agent(
    role="Expert Writing Critic",
    # 提供反馈并批评博客文章草稿。确保语气和写作风格引人入胜，简洁明了。
    goal="Provide feedback and criticize blog post drafts. Make sure that the tone and writing style is compelling, simple and concise",
    # 您擅长给技术作家提供反馈。您能够辨别博客文本是否精炼、简单或足够引人入胜。您知道如何提供有益的反馈，可以改善任何文本。
    # 您知道如何确保文本保持技术性和见解性，同时使用通俗易懂的术语
    backstory="""You are an Expert at providing feedback to the technical writers. You can tell when a blog text isn't concise,
    simple or engaging enough. You know how to provide helpful feedback that can improve any text. You know how to make sure that text 
    stays technical and insightful by using layman terms. Answer in Chinese. 
    """,
    verbose=True,
    allow_delegation=True,
    #llm=mistral,  # remove to use default gpt-4
    #llm=groq_client,
)

task_report = Task(
    description="""Use and summarize scraped data from subreddit LocalLLama to make a detailed report on the latest rising projects in AI. Use ONLY 
    scraped data from LocalLLama to generate the report. Your final answer MUST be a full analysis report, text only, ignore any code or anything that 
    isn't text. The report has to have bullet points and with 5-10 exciting new AI projects and tools. Write names of every tool and project. 
    Each bullet point MUST contain 3 sentences that refer to one specific ai company, product, model or anything you found on subreddit LocalLLama.  
    """,
    agent=explorer,
    expected_output="A detailed report on the latest rising projects in AI, generated from scraped data from LocalLLama subreddit. The report contains bullet points with 5-10 exciting new AI projects and tools, and each bullet point contains 3 sentences that refer to one specific ai company, product, model or anything found on subreddit LocalLLama. Report output in Chinese"
)

task_blog = Task(
    description="""Write a blog article with text only and with a short but impactful headline and at least 10 paragraphs. Blog should summarize 
    the report on latest ai tools found on localLLama subreddit. Style and tone should be compelling and concise, fun, technical but also use 
    layman words for the general public. Name specific new, exciting projects, apps and companies in AI world. Don't 
    write "**Paragraph [number of the paragraph]:**", instead start the new paragraph in a new line. Write names of projects and tools in BOLD.
    ALWAYS include links to projects/tools/research papers. ONLY include information from LocalLLAma.
    For your Outputs use the following markdown format:
    ```
    ## [Title of post](link to project)
    - Interesting facts
    - Own thoughts on how it connects to the overall theme of the newsletter
    ## [Title of second post](link to project)
    - Interesting facts
    - Own thoughts on how it connects to the overall theme of the newsletter
    ```
    """,
    agent=writer,
    expected_output="A blog article with text only and with a short but impactful headline and at least 10 paragraphs. Blog should summarize the report on latest ai tools found on localLLama subreddit. Style and tone should be compelling and concise, fun, technical but also use layman words for the general public. Name specific new, exciting projects, apps and companies in AI world. Don't write '**Paragraph [number of the paragraph]:**', instead start the new paragraph in a new line. Write names of projects and tools in BOLD. ALWAYS include links to projects/tools/research papers. ONLY include information from LocalLLAma. Blog content output in Chinese",
)

task_critique = Task(
    description="""The Output MUST have the following markdown format:
    ```
    ## [Title of post](link to project)
    - Interesting facts
    - Own thoughts on how it connects to the overall theme of the newsletter
    ## [Title of second post](link to project)
    - Interesting facts
    - Own thoughts on how it connects to the overall theme of the newsletter
    ```
    Make sure that it does and if it doesn't, rewrite it accordingly.
    """,
    agent=critic,
    expected_output="The Output MUST have the following markdown format: ## [Title of post](link to project) - Interesting facts - Own thoughts on how it connects to the overall theme of the newsletter ## [Title of second post](link to project) - Interesting facts - Own thoughts on how it connects to the overall theme of the newsletter Make sure that it does and if it doesn't, rewrite it accordingly."
)

# 实例化crew的代理
crew = Crew(
    agents=[explorer, writer, critic],
    tasks=[task_report, task_blog, task_critique],
    verbose=2,
    # 顺序流程将一个接一个地执行任务，并且前一个任务的结果作为额外内容传递到下一个任务
    process=Process.sequential,  
)

# 启动crew开始工作
result = crew.kickoff()

print("######################")
print(result)
