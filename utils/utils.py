from configs.lessons_config import *

def get_text_list_lessons_with_code():
    ret_text = ''

    for i in lessons:
        ret_text += f'{i} - {lessons[i]}\n'

    return ret_text
