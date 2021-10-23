import asyncio
import click
import json
import logging

import aiohttp as aiohttp
import requests
import csv


async def get_question_info(client, question):
    query = """
    query questionData($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n    questionId\n    questionFrontendId\n    boundTopicId\n    title\n    titleSlug\n    content\n    translatedTitle\n    translatedContent\n    isPaidOnly\n    difficulty\n    likes\n    dislikes\n    isLiked\n    similarQuestions\n    contributors {\n      username\n      profileUrl\n      avatarUrl\n      __typename\n    }\n    langToValidPlayground\n    topicTags {\n      name\n      slug\n      translatedName\n      __typename\n    }\n    companyTagStats\n    codeSnippets {\n      lang\n      langSlug\n      code\n      __typename\n    }\n    stats\n    hints\n    solution {\n      id\n      canSeeDetail\n      __typename\n    }\n    status\n    sampleTestCase\n    metaData\n    judgerAvailable\n    judgeType\n    mysqlSchemas\n    enableRunCode\n    enableTestMode\n    envInfo\n    libraryUrl\n    __typename\n  }\n}\n
    """
    body = {"operationName": "questionData",
            "variables": {"titleSlug": question},
            "query": query}

    url = "https://leetcode.com/graphql"

    async with client.post(url, json=body) as resp:
        response = await resp.read()

    try:
        return json.loads(response)["data"]["question"]
    except:
        logging.info('Returned response is not json deserializable')


def _get_all_leetcode_questions():
    url = "https://leetcode.com/api/problems/all/"
    questions = []
    response = requests.get(url)

    r_json = response.json()
    for slug in r_json["stat_status_pairs"]:
        questions.append(slug["stat"]["question__title_slug"])
    return questions


async def get_all_leetcode_questions():
    all_questions = _get_all_leetcode_questions()
    async with aiohttp.ClientSession() as client:
        all_questions_info = await asyncio.gather(*[
            asyncio.ensure_future(get_question_info(client, question))
            for question in all_questions
        ])
    return all_questions_info


def to_csv(questions):
    keys = ['id', 'title', 'likes', 'dislikes', 'like/dislikes_ratio', 'difficulty']

    data = list(map(lambda question_dict: (
        {'id': question_dict.get('questionFrontendId'),
         'title': question_dict.get('title'),
         'likes': question_dict.get('likes'),
         'dislikes': question_dict.get('dislikes'),
         'like/dislikes_ratio': question_dict.get('likes') / (
             question_dict.get('dislikes') if question_dict.get('dislikes') != 0 else 1),
         'difficulty': question_dict.get('difficulty')
         }), questions))

    with open('leetcode.csv', 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)


@click.command()
@click.option('--difficulty', default=['Easy', 'Medium', 'Hard'], help='difficulty of questions', multiple=True)
def questions_filtration(difficulty):
    print(difficulty)
    filter_criteria = {'difficulty': difficulty}
    loop = asyncio.get_event_loop()
    questions_info = loop.run_until_complete(get_all_leetcode_questions())

    filtered_questions = list(filter(
        lambda question_dict: question_dict and question_dict.get('difficulty') in filter_criteria.get('difficulty'),
        questions_info)
    )
    sorted_result = sorted(filtered_questions, key=lambda question_dict: (
        question_dict.get('likes'),
        question_dict.get('likes') / (question_dict.get('dislikes') if question_dict.get('dislikes') != 0 else 1)
    ), reverse=True)
    to_csv(sorted_result)


questions_filtration()
