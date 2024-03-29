import praw
from googletrans import Translator

# 创建Reddit对象
reddit = praw.Reddit(
    		client_id="2v3pe84Oh5l-gunXUifPgg",
            client_secret="0C1wLwkZxE3ygGlGhcY8LALh4461wQ",
            user_agent="lg_news_bot",
    )

# 获取一个帖子
submission = reddit.submission(url='https://www.reddit.com/r/LocalLLaMA/comments/1bpt49b/is_starlinglm7bbeta_that_good/')

# 获取帖子的所有回复
submission.comments.replace_more(limit=None)
all_comments = submission.comments.list()

# 创建一个翻译器对象
translator = Translator()

# 打开一个文件来保存回复内容
with open('comments_cn.txt', 'w', encoding='utf-8') as file:
    # 将所有回复的内容翻译为中文并写入文件
    for comment in all_comments:
        #file.write(comment.body + '\n')
        if comment != "\n":
            try:
                translated_comment = translator.translate(comment.body, src='en', dest='zh-cn').text
                file.write(translated_comment + '\n')
            except Exception as e:
                print(f"翻译失败：{e}，内容为{comment.body}")