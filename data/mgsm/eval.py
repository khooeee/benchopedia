"""MGSM native chain-of-thought prompts and exact numeric grading.

The first six worked examples per language come from the pinned MGSM
distribution and are attributed in redistribution-review.md.
https://github.com/google-research/url-nlp/blob/452a21ad3dae5668c06ceeac21ff073e1e40f9be/mgsm/exemplars.py
https://arxiv.org/abs/2210.03057v1
"""

from decimal import Decimal
import re

ATTEMPTS = 2
NUMBER_RE = re.compile(r"-?\d+(?:,\d{3})*(?:\.\d+)?")


def messages(task):
    language = task["key"].split("-", 1)[0]
    question_label, answer_label, examples = NATIVE_PROMPTS[language]
    prompt = f"{examples}{question_label}{task['prompt']}\n{answer_label}"
    return [{"role": "user", "content": prompt}]


def grade(task, output):
    language = task["key"].split("-", 1)[0]
    question_label, _, _ = NATIVE_PROMPTS[language]
    # Stop at the first continuation of the example sequence.
    response = output.split(question_label.strip(), 1)[0]
    numbers = NUMBER_RE.findall(response)
    if not numbers:
        return "unparseable", None
    answer = numbers[-1].replace(",", "")
    reference = task["solution"].replace(",", "")
    return ("pass" if Decimal(answer) == Decimal(reference) else "fail"), answer


# Localized question label, answer label, and rendered six-shot prefix.
# Keep this data with the evaluator so each run snapshots its exact prompts.
NATIVE_PROMPTS = {
    'bn': (
        'প্রশ্ন: ',
        'ধাপে ধাপে উত্তর:',
        'প্রশ্ন: রজারের 5টি টেনিস বল আছে। সে আরও 2 ক্যান টেনিস বল কিনেছে। প্রতিটি ক্যানে 3টি করে টেনিস বল আছে। তার কাছে এখন কতগুলি টেনিস বল আছে?\n'
        'ধাপে ধাপে উত্তর: রজারের প্রথমে 5টি বল ছিল। 2টি ক্যানের প্রতিটিতে 3টে টেনিস বল মানে 6টি টেনিস বল। 5 + 6 = 11। উত্তর হল 11।\n'
        '\n'
        'প্রশ্ন: সার্ভার কক্ষে নয়টি কম্পিউটার ছিল। সোমবার থেকে বৃহস্পতিবার প্রতিদিন আরও পাঁচটি করে কম্পিউটার স্থাপন করা হয়েছিল। সার্ভার কক্ষে এখন কতগুলি কম্পিউটার আছে?\n'
        'ধাপে ধাপে উত্তর: সোমবার থেকে বৃহস্পতিবার 4দিন হয়। প্রতিদিন 5টি করে কম্পিউটার যোগ করা হয়েছে। যার অর্থ মোট 4 * 5 = 20টি কম্পিউটার যোগ করা হয়েছে। শুরুতে 9টি কম্পিউটার ছিল, তাই এখন 9 + 20 = 29টি কম্পিউটার রয়েছে। উত্তর হল 29।\n'
        '\n'
        'প্রশ্ন: লিয়ার 32টি চকোলেট ছিল এবং তার বোনের ছিল 42টি। যদি তারা 35টি খেয়ে থাকে, তাহলে তাদের কাছে মোট কতগুলি অবিশিষ্ট আছে?\n'
        'ধাপে ধাপে উত্তর: লিয়ার 32টি চকোলেট ছিল এবং লিয়ার বোনের ছিল 42টি। যার অর্থ শুরুতে 32 + 42 = 74টি চকোলেট ছিল। 35টি খাওয়া হয়ে গেছে। তাই তাদের কাছে মোট 74 - 35 = 39টি চকোলট আছে। উত্তর হল 39।\n'
        '\n'
        'প্রশ্ন: শনের পাঁচটি খেলনা আছে। ক্রিসমাস উপলক্ষে সে তার মাতা ও পিতা উভয়ের থেকে দুটি করে খেলনা পেয়েছে। তার কাছে এখন কতগুলি খেলনা আছে?\n'
        'ধাপে ধাপে উত্তর: তার কাছে 5টি খেলনা আছে। সে তার মাতার থেকে 2টি খেলনা পেয়েছিল অতএব, এরপর তার 5 + 2 = 7টি খেলনা হয়েছে। তারপর সে তার পিতার থেকে 2টি খেলনা পেয়েছিল, তাই তার মোট 7 + 2 = 9 টি খেলনা হয়েছে। উত্তর হল 9।\n'
        '\n'
        'প্রশ্ন: মাইকেলের 58টি গলফ বল ছিল। মঙ্গলবার, সে 23টি গলফ বল হারিয়েছিল। বুধবার, সে আরও 2টি বল হারিয়েছিল। বুধবারের শেষে তার কাছে কয়টি গলফ বল ছিল?\n'
        'ধাপে ধাপে উত্তর: শুরুতে মাইকেলের কাছে 58টি গলফ বল ছিল এবং সে 23টি বল হারিয়েছিল, তাই তার 58 - 23 = 35টি বল আছে। আরও 2টি বল হারানোর পর, তার এখন 35 - 2 = 33টি বল আছে। উত্তর হল 33।\n'
        '\n'
        'প্রশ্ন: অলিভিয়ার $23 আছে। সে পাঁচটি ব্যাগেল কিনেছিল যার প্রতিটির মূল্য $3। তার কাছে কত অর্থ অবশিষ্ট আছে?\n'
        'ধাপে ধাপে উত্তর: প্রতিটি ব্যাগেলের মূল্য $3 হলে 5টি ব্যাগেলের মূল্য হওয়া উচিৎ 5 *3 = 15 ডলার। শুরুতে অলিভিয়ার কাছে $23 ছিল, তাই বর্তমানে তার কাছে 23 - 15 = 8 ডলার অবশিষ্ট আছে। উত্তর হল 8।\n'
        '\n',
    ),
    'de': (
        'Frage: ',
        'Schritt-für-Schritt-Antwort:',
        'Frage: Roger hat 5 Tennisbälle. Er kauft noch 2 Dosen Tennisbälle. In jeder Dose sind 3 Tennisbälle. Wie viele Tennisbälle hat er jetzt?\n'
        'Schritt-für-Schritt-Antwort: Roger begann mit 5 Bällen. 2 Dosen von jeweils 3 Tennisbällen macht 6 Tennisbälle. 5 + 6 = 11. Die Antwort ist 11.\n'
        '\n'
        'Frage: Es waren neun Computer im Serverraum. Von Montag bis Donnerstag wurden jeden Tag noch fünf Computer installiert. Wie viele Computer sind jetzt im Serverraum?\n'
        'Schritt-für-Schritt-Antwort: Von Montag bis Donnerstag sind es 4 Tage. Jeden Tag kamen 5 neue Computer hinzu. Das macht insgesamt 4 x 5 = 20 Computer, die hinzugefügt wurden. Am Anfang waren es 9 Computer, also sind es jetzt 9 + 20 =29 Computer. Die Antwort lautet 29.\n'
        '\n'
        'Frage: Leah hat 32 Pralinen und ihre Schwester hat 42. Wenn sie 35 essen, wie viele sind dann insgesamt noch übrig?\n'
        'Schritt-für-Schritt-Antwort: Leah hat 32 Pralinen und Leahs Schwester 42. Das bedeutet, dass es ursprünglich 32 + 42 =74 Pralinen waren. 35 wurden gegessen. Also haben sie insgesamt noch 74 - 35 = 39 Pralinen übrig. Die Antwort lautet 39.\n'
        '\n'
        'Frage: Shawn hat fünf Spielzeuge. Zu Weihnachten hat er von seiner Mama und seinem Papa jeweils zwei Spielzeuge bekommen. Wie viele Spielzeuge hat er jetzt?\n'
        'Schritt-für-Schritt-Antwort: Er hat 5 Spielzeuge. Er hat 2 von seiner Mama bekommen, sodass er nun 5 + 2 = 7 Spielzeuge hat. Dann hat er noch 2 von seinem Papa bekommen, also hat er insgesamt 7 + 2 = 9 Spielzeuge. Die Antwort lautet 9.\n'
        '\n'
        'Frage: Michael hat 58 Golfbälle. Am Dienstag hat er 23 Golfbälle verloren. Am Mittwoch hat er 2 weitere verloren. Wie viele Golfbälle hat er Mittwoch am Ende des Tages?\n'
        'Schritt-für-Schritt-Antwort: Michael hatte anfangs 58 Golfbälle und hat 23 verloren, sodass er 58 - 23 = 35 hat. Nachdem er 2 weitere verloren hat, hat er jetzt 35 - 2 = 33 Bälle. Die Antwort lautet 33.\n'
        '\n'
        'Frage: Olivia hat 23 US-Dollar. Sie hat fünf Bagels für 3 US-Dollar pro Stück gekauft. Wie viel Geld hat sie übrig?\n'
        'Schritt-für-Schritt-Antwort: 5 Bagels für 3 US-Dollar pro Stück kosten 5 x 3 = 15 Dollar. Olivia hat anfangs 23 US-Dollar, also hat sie jetzt 23 - 15 = 8 Dollar übrig. Die Antwort lautet 8.\n'
        '\n',
    ),
    'en': (
        'Question: ',
        'Step-by-Step Answer:',
        'Question: Roger has 5 tennis balls. He buys 2 more cans of tennis balls. Each can has 3 tennis balls. How many tennis balls does he have now?\n'
        'Step-by-Step Answer: Roger started with 5 balls. 2 cans of 3 tennis balls each is 6 tennis balls. 5 + 6 = 11. The answer is 11.\n'
        '\n'
        'Question: There were nine computers in the server room. Five more computers were installed each day, from monday to thursday. How many computers are now in the server room?\n'
        'Step-by-Step Answer: There are 4 days from monday to thursday. 5 computers were added each day. That means in total 4 * 5 = 20 computers were added. There were 9 computers in the beginning, so now there are 9 + 20 = 29 computers. The answer is 29.\n'
        '\n'
        'Question: Leah had 32 chocolates and her sister had 42. If they ate 35, how many pieces do they have left in total?\n'
        'Step-by-Step Answer: Leah had 32 chocolates and Leah’s sister had 42. That means there were originally 32 + 42 = 74 chocolates. 35 have been eaten. So in total they still have 74 - 35 = 39 chocolates. The answer is 39.\n'
        '\n'
        'Question: Shawn has five toys. For Christmas, he got two toys each from his mom and dad. How many toys does he have now?\n'
        'Step-by-Step Answer: He has 5 toys. He got 2 from mom, so after that he has 5 + 2 = 7 toys. Then he got 2 more from dad, so in total he has 7 + 2 = 9 toys. The answer is 9.\n'
        '\n'
        'Question: Michael had 58 golf balls. On tuesday, he lost 23 golf balls. On wednesday, he lost 2 more. How many golf balls did he have at the end of wednesday?\n'
        'Step-by-Step Answer: Michael started with 58 golf balls and lost 23, so he has 58 - 23 = 35. After he lost 2 more, he has 35 - 2 = 33 balls now. The answer is 33.\n'
        '\n'
        'Question: Olivia has $23. She bought five bagels for $3 each. How much money does she have left?\n'
        'Step-by-Step Answer: 5 bagels for $3 each should cost 5 * 3 = 15 dollars. Olivia had $23 in the beginning, so now she has 23 - 15 = 8 dollars left. The answer is 8.\n'
        '\n',
    ),
    'es': (
        'Pregunta: ',
        'Respuesta paso a paso:',
        'Pregunta: Roger tiene 5 pelotas de tenis. Compra 2 tubos más de pelotas de tenis. Cada tubo contiene 3 pelotas de tenis. ¿Cuántas pelotas de tenis tiene ahora?\n'
        'Respuesta paso a paso: Roger comenzó con 5 pelotas. 2 tubos de 3 pelotas de tenis cada uno equivale a 6 pelotas de tenis. 5 + 6 = 11. La respuesta es 11.\n'
        '\n'
        'Pregunta: Había nueve computadoras en la sala de servidores. Se instalaron cinco computadoras cada día, de lunes a jueves. ¿Cuántas computadoras hay ahora en la sala de servidores?\n'
        'Respuesta paso a paso: Hay 4 días de lunes a jueves. Se agregaron 5 computadoras cada día. Eso significa que en total se agregaron 4 * 5 = 20 computadoras. Al principio, había 9 computadoras, por lo que ahora hay 9 + 20 = 29 computadoras. La respuesta es 29.\n'
        '\n'
        'Pregunta: Leah tenía 32 chocolates y su hermana tenía 42. Si se comieron 35, ¿cuántos chocolates les quedan en total?\n'
        'Respuesta paso a paso: Leah tenía 32 chocolates y la hermana de Leah tenía 42. Quiere decir que originalmente había 32 + 42 = 74 chocolates. Se comieron 35. Por lo tanto, en total todavía tienen 74 - 35 = 39 chocolates. La respuesta es 39.\n'
        '\n'
        'Pregunta: Shawn tiene cinco juguetes. Para Navidad, recibió dos juguetes de su mamá y dos de su papá. ¿Cuántos juguetes tiene ahora?\n'
        'Respuesta paso a paso: Tiene 5 juguetes. Recibió 2 de la mamá, por lo que después de eso tiene 5 + 2 = 7 juguetes. Luego, recibió 2 más del papá, así que en total tiene 7 + 2 = 9 juguetes. La respuesta es 9.\n'
        '\n'
        'Pregunta: Michael tenía 58 pelotas de golf. El martes, perdió 23 pelotas de golf. El miércoles, perdió 2 más. ¿Cuántas pelotas de golf tenía al final del miércoles?\n'
        'Respuesta paso a paso: Michael comenzó con 58 pelotas de golf y perdió 23, por lo tanto tiene 58 - 23 = 35. Después de perder 2 más, ahora tiene 35 - 2 = 33 pelotas. La respuesta es 33.\n'
        '\n'
        'Pregunta: Olivia tiene $23. Compró cinco roscas a $3 cada una. ¿Cuánto dinero le queda?\n'
        'Respuesta paso a paso: 5 roscas a $3 cada una deben costar 5 * 3 = 15 dólares. Olivia tenía $23 al principio, por lo tanto ahora le quedan 23 - 15 = 8 dólares. La respuesta es 8.\n'
        '\n',
    ),
    'fr': (
        'Question : ',
        'Réponse étape par étape :',
        'Question : Roger a 5 balles de tennis. Il achète 2 autres boîtes de balles de tennis en plus. Si chaque boîte contient 3 balles de tennis, combien de balles de tennis a-t-il maintenant ?\n'
        'Réponse étape par étape : Roger a commencé avec 5 balles. 2 boîtes de 3 balles de tennis chacune représentent 6 balles de tennis. 5 + 6 = 11. La réponse est 11.\n'
        '\n'
        "Question : Il y avait neuf ordinateurs dans la salle des serveurs. Cinq ordinateurs supplémentaires ont été installés chaque jour, du lundi au jeudi. Combien d'ordinateurs y a-t-il maintenant dans la salle des serveurs ?\n"
        "Réponse étape par étape : De lundi à jeudi, il y a 4 jours. 5 ordinateurs ont été ajoutés par jour. Cela signifie qu'au total, 4 x 5 = 20 ordinateurs ont été ajoutés. Comme il y avait 9 ordinateurs au départ, il y a maintenant 9 + 20 = 29 ordinateurs. La réponse est 29.\n"
        '\n'
        'Question : Léa avait 32 chocolats et sa sœur en avait 42. Si elles en ont mangé 35, combien de morceaux leur reste-t-il en tout ?\n'
        "Réponse étape par étape : Léa avait 32 chocolats et sa sœur en avait 42. Cela signifie qu'il y avait à l'origine 32 + 42 = 74 chocolats. 35 chocolats ont été mangés. Il leur en reste donc au total 74 - 35 = 39 chocolats. La réponse est 39.\n"
        '\n'
        'Question : Shawn a cinq jouets. Pour Noël, papa et maman lui ont offert deux jouets chacun. Combien de jouets a-t-il maintenant ?\n'
        "Réponse étape par étape : Il a 5 jouets. Il en a reçu 2 de maman, ce qui fait qu'il a 5 + 2 = 7 jouets. Ensuite, il a reçu 2 autres jouets de papa. Cela fait donc un total de 7 + 2 = 9 jouets. La réponse est 9.\n"
        '\n'
        'Question : Michael avait 58 balles de golf. Mardi, il a perdu 23 balles de golf. Mercredi, il en a perdu 2 autres. De combien de balles de golf disposait-il à la fin du mercredi ?\n'
        'Réponse étape par étape : Michael a commencé avec 58 balles de golf et en a perdu 23. Il lui reste donc 58 - 23 = 35. Après en avoir perdu 2 autres, il lui reste 35 - 2 = 33 balles. La réponse est 33.\n'
        '\n'
        "Question : Olivia a 23 $. Elle a acheté cinq bagels à 3 $ chacun. Combien d'argent lui reste-t-il ?\n"
        'Réponse étape par étape : 5 bagels à 3 $ chacun coûtent 5 x 3 = 15 dollars. Olivia avait 23 dollars au départ, il lui reste donc 23 - 15 = 8 dollars. La réponse est 8.\n'
        '\n',
    ),
    'ja': (
        '問題：',
        'ステップごとの答え：',
        '問題：ロジャーは5個のテニスボールがあります。テニスボールの缶を2つ追加で買います。それぞれの缶には3つのテニスボールが入っています。彼は今いくつのテニスボールがありますか？\n'
        'ステップごとの答え：ロジャーは最初5個のボールがありました。テニスボール3個入りの缶が2つあれば、テニスボールは6個あります。5+6=11。答えは11です。\n'
        '\n'
        '問題：サーバールームには9台のコンピューターがありました。月曜日から木曜日まで毎日5台のコンピューターをインストールしました。今サーバールームには難題のコンピューターがありますか？\n'
        'ステップごとの答え：月曜から木曜まで4日あります。毎日5台のコンピューターが追加されます。つまり、全部で4*5=20台のコンピューターが追加されました。最初に9台のコンピューターがあったので、今は9+20=29台のコンピューターとなります。答えは29です。\n'
        '\n'
        '問題：リアは32個のチョコレートを持っていました、彼女の妹は42個持っていました。彼女達が35個食べたとしたら、全部で何個残っていますか？\n'
        'ステップごとの答え：リアは32個のチョコレートを持っており、リアの妹は42個持っていた。つまり、元々32+42=74個のチョコレートがあった。35個が食べられた。だから全部で、彼女たちには74-35=39個のチョコレートが残っている。答えは39個。\n'
        '\n'
        '問題：ショーンは5個のおもちゃを持っています。クリスマスに、彼は父と母からそれぞれ2つずつおもちゃをもらいました。今彼はいくつのおもちゃがありますか？\n'
        'ステップごとの答え：彼は5個おもちゃを持っています。母から2つもらった後は、5+2=7個のおもちゃがあります。その後父から2つさらにもらい、全部で彼は、7+2=9個のおもちゃがあります。答えは9個です。\n'
        '\n'
        '問題：マイケルは58個のゴルフボールを持っています。火曜日、彼は\n'
        '23個のゴルフボールを失くしました。水曜日、さらに2個失くしました。水曜日の終わりには、彼は何このゴルフボールを持っていましたか？\n'
        'ステップごとの答え：マイケルは最初58個のゴルフボールがあり、23個なくしました、だから彼は58-23=35個残っています。彼があと2個なくした後、彼は今35-2=33個残っています。答えは33個です。\n'
        '\n'
        '問題：オリビアには$23あります。彼女はそれぞれ$3のベーグルを5つ買いました。彼女にはいくらのお金が残っていますか？\n'
        'ステップごとの答え：$3のベーグルは5個で、5*3=15ドルになるはずです。オリビアは最初$23あったので、今彼女には23-15=8ドル残っています。答えは8です。\n'
        '\n',
    ),
    'ru': (
        'Задача: ',
        'Пошаговое решение:',
        'Задача: у Роджера 5 теннисных мячей. Он покупает еще 2 банки теннисных мячей. В каждой банке 3 теннисных мяча. Сколько теннисных мячей у него сейчас?\n'
        'Пошаговое решение: в начале у Роджера было 5 мячей. 2 банки по 3 теннисных мяча каждая — это 6 теннисных мячей. 5 + 6 = 11. Ответ — 11.\n'
        '\n'
        'Задача: в серверной было девять компьютеров. Каждый день с понедельника по четверг устанавливалось еще по пять компьютеров. Сколько компьютеров сейчас в серверной?компьютеров.\n'
        'Пошаговое решение: с понедельника по четверг прошло 4 дня. Каждый день добавляли по 5 компьютеров. То есть всего добавили 4 * 5 = 20 компьютеров. Вначале было 9 компьютеров, значит, теперь стало 9 + 20 = 29 компьютеров. Ответ — 29.\n'
        '\n'
        'Задача: у Лии было 32 шоколадных конфеты, а у ее сестры — 42. Если 35 они съели, сколько всего штук у них осталось?\n'
        'Пошаговое решение: у Лии было 32 шоколадных конфеты, а у сестры Лии — 42. Значит, первоначально было 32 + 42 = 74 шоколадных конфеты. 35 съели. Значит, всего осталось 74 - 35 = 39 шоколадных конфет. Ответ — 39.\n'
        '\n'
        'Задача: у Шона было пять игрушек. На Рождество он получил по две игрушки от мамы и от папы. Сколько у него сейчас игрушек?\n'
        'Пошаговое решение: у него было 5 игрушек. Он получил 2 от мамы, и после этого у него стало 5 + 2 = 7 игрушек. Потом он получил еще 2 от папы, так что в общей сложности у него стало 7 + 2 = 9 игрушек. Ответ — 9.\n'
        '\n'
        'Задача: у Майкла было 58 мячей для гольфа. Во вторник он потерял 23 мяча для гольфа. В среду он потерял еще 2. Сколько мячей для гольфа осталось у него к концу среды?\n'
        'Пошаговое решение: вначале у Майкла было 58 мячей для гольфа, 23 он потерял, и у него осталось 58 - 23 = 35. После этого он потерял еще 2, и теперь у него осталось 35 - 2 = 33 мяча. Ответ — 33.\n'
        '\n'
        'Задача: у Оливии было 23 $. Она купила пять рогаликов по 3 $. Сколько денег у нее осталось?\n'
        'Пошаговое решение: 5 рогаликов по 3 $ стоят 5 * 3 = 15 долларов. Вначале у Оливии было 23 $, значит, теперь у нее осталось 23 - 15 = 8 $. Ответ — 8.\n'
        '\n',
    ),
    'sw': (
        'Swali: ',
        'Jibu la Hatua kwa Hatua:',
        'Swali: Roger ana mipira 5 ya tenisi. Ananunua mikebe 2 zaidi ya mipira ya tenisi. Kila mkebe una mipira 3 ya tenisi. Ana mipira mingapi ya tenisi kwa sasa?\n'
        'Jibu la Hatua kwa Hatua: Roger alianza kwa mipira 5. Mikebe 2 yenye mipira 3 ya tenisi kila oja ni mipira 6 ya tenisi. 5 + 6 = 11. Jibu ni 11.\n'
        '\n'
        'Swali: Kuna kompyuta tisa katika chumba cha seva. Kompyuta tano zaidi zilisakinishwa kila siku, kuanzia Jumatatu hadi Alhamisi. Kuna kompyuta ngapi wkenye chumba cha seva kufikia sasa?\n'
        'Jibu la Hatua kwa Hatua: Kuna siku 4 kuanzia Jumatatu mpaka Alhamisi. Kompyuta 5 ziliongezwa kila siku. Hiyo inamaanisha kuwa kwa jumla kompyuta 4 * 5 = 20 ziliongezwa. Kulikuwa na kompyuta 9 mwanzoni, hivyo sasa kuna kompyuta 9 + 20 = 29. Jibu ni 29.\n'
        '\n'
        'Swali: Leah alikuwa na chokoleti 32 na dadake alikuwa na 42. Iwapo walikula 35, wamesalia na chokoleti ngapi kwa jumla?\n'
        'Jibu la Hatua kwa Hatua: Lea alikuwa na chokoleti 32 na dadake Leah alikuwa na 42. Hiyo inamaanisha kuwa awali kulikuwa na chokoleti 32 + 42 + 74. 35 zimeliwa. Hivyo kwa jumla bado kuna chokoleti 74 - 35 = 39. Jibu ni 39.\n'
        '\n'
        'Swali: Shawn ana wanasesere watano. Siku ya Krismasi, alipata wanasesere wawili kutoka kwa mamake na babake kila mmoja. Sasa ana wanasesere wangapi kwa sasa?\n'
        'Jibu la Hatua kwa Hatua: Ana wanasesere 5. Alipata 2 kutoka kwa mama, hivyo baada ya hapo alikuwa na wanasesere 5 + 2 = 7. Kisha alipata 2 zaidi kutoka kwa baba, hivyo kwa jumla alikuwa na wanasesere 7 + 2 = 9. Jibu ni 9.\n'
        '\n'
        'Swali: Michael alikuwa na mipira 58 ya gofu. Jumanne, alipoteza mipira 23 ya gofu. Jumatano, alipoteza mipira 2 zaidi. Alikuwa na mipira mingapi ya gofu kufikia mwishoni mwa Jumatano?\n'
        'Jibu la Hatua kwa Hatua: Michael alianza na mipira 58 ya gofu na akapoteza 23, hivyo ana 58 - 23 = 35. Baadaye alipoteza 2 zaidi, sasa ana mipira 35 - 2 = 33. Jibu ni 33.\n'
        '\n'
        'Swali: Olivia ana $23. Alinunua bageli tano kwa $3 kila moja. Amesalia na pesa ngapi?\n'
        'Jibu la Hatua kwa Hatua: Bageli 5 za $3 kila moja zinafaa kugharimu 5 * 3 = dola 15. Olivia alikuwa na $23 mwanzoni, sasa amesalia na dola 23 - 15 = 8. Jibu ni 8.\n'
        '\n',
    ),
    'te': (
        'ప్రశ్న: ',
        'దశలవారీగా సమాధానం:',
        'ప్రశ్న: రోజర్ వద్ద 5 టెన్నిస్ బంతులు ఉన్నాయి. అతడు మరో 2 క్యాన్\u200cల టెన్నిస్ బంతులు కొనుగోలు చేశాడు. ప్రతి క్యాన్\u200cలో 3 టెన్నిస్ బంతులున్నాయి. ఇప్పుడు అతడి వద్ద ఎన్ని టెన్నిస్ బంతులు ఉన్నాయి?\n'
        'దశలవారీగా సమాధానం: రోజర్ 5 బంతులతో ప్రారంభించాడు. 2 క్యాన్\u200cల్లో ఒక్కదానిలో 3 టెన్నిస్ బంతులు అంటే 6 టెన్నిస్ బంతులు ఉన్నాయి. 5+6=11. సమాధానం 11.\n'
        '\n'
        'ప్రశ్న: సర్వర్ రూమ్\u200cలో తొమ్మిది కంప్యూటర్\u200cలు ఉన్నాయి. సోమవారం నుంచి గురువారం వరకు ప్రతిరోజూ మరో ఐదు కంప్యూటర్\u200cలు ఇన్\u200cస్టాల్ చేయబడ్డాయి. సర్వర్ రూమ్\u200cలో ఇప్పుడు ఎన్ని కంప్యూటర్\u200cలు ఉన్నాయి?కంప్యూటర్\u200cలుకంప్యూటర్\u200cలు\n'
        'దశలవారీగా సమాధానం: సోమవారం నుంచి గురువారం వరకు 4 రోజులున్నాయి. ప్రతిరోజూ 5 కంప్యూటర్\u200cలు జోడించబడ్డాయి. అంటే మొత్తం 4*5=20 కంప్యూటర్\u200cలు జోడించబడ్డాయి. ప్రారంభంలో 9 కంప్యూటర్\u200cలు ఉన్నాయి, అందువల్ల ఇప్పుడు అవి 9+20=29 కంప్యూటర్\u200cలు సమాధానం 29.\n'
        '\n'
        'ప్రశ్న: లియా వద్ద 32 చాక్లెట్\u200cలు మరియు ఆమె సోదరి వద్ద 42 ఉన్నాయి. వారు 35 తిన్నట్లయితే, మొత్తం మీద వారి వద్ద ఎన్ని పీస్\u200cలు మిగిలి ఉన్నాయి?\n'
        'దశలవారీగా సమాధానం: లియా వద్ద 32 చాక్లెట్\u200cలు ఉన్నాయి, లియా సోదరి వద్ద 42 చాక్లెట్\u200cలు ఉన్నాయి. అంటే వారి వద్ద వాస్తవంగా 32+42= 74 చాక్లెట్\u200cలు ఉన్నాయి. 35 చాక్లెట్\u200cలను తిన్నారు. అందువల్ల వారి వద్ద మొత్తం 74-35= 39 చాక్లెట్\u200cలు ఉన్నాయి. సమాధానం 39.చాక్లెట్\u200cలుచాక్లెట్\u200cలుచాక్లెట్\u200cలు\n'
        '\n'
        'ప్రశ్న: షాన్ వద్ద ఐదు బొమ్మలు ఉన్నాయి. అతడు క్రిస్టమస్ కొరకు తన అమ్మ మరియు నాన్నల నుంచి రెండేసి బొమ్మల చొప్పున పొందాడు. ఇప్పుడు అతడి వద్ద ఎన్ని బొమ్మలు ఉన్నాయి?\n'
        'దశలవారీగా సమాధానం: అతడి వద్ద 5 బొమ్మలు ఉన్నాయి. అతడు అమ్మ దగ్గర నుంచి 2 పొందాడు, కాబట్టి ఆ తరువాత అతడి వద్ద 5+2=7 బొమ్మలున్నాయి. తరువాత తండ్రి వద్ద నుంచి అతడు మరో 2 పొందాడు. అందువల్ల మొత్తం మీద అతడి వద్ద 7+2=9 బొమ్మలున్నాయి. సమాధానం 9.బొమ్మలున్నాయి.\n'
        '\n'
        'ప్రశ్న: మైకెల్ వద్ద 58 గోల్ఫ్ బాల్స్ ఉన్నాయి. మంగళవారం నాడు, అతడు 23 గోల్ఫ్ బాల్స్\u200cని పొగొట్టుకున్నాడు. బుధవారం నాడు, అతడు మరో 2 పోగొట్టుకున్నాడు. బుధవారం చివరికి అతడి వద్ద ఎన్ని గోల్ఫ్ బాల్\u200cలు ఉన్నాయి?\n'
        'దశలవారీగా సమాధానం: మైకెల్ 58 గోల్ఫ్ బాల్స్\u200cతో ప్రారంభించాడు మరియు 23 పోగొట్టుకున్నాడు, అందువల్ల అతడి వద్ద 58-23=35 ఉన్నాయి. అతడు మరో 2 కోల్పోయిన తరువాత, అతడి వద్ద ఇప్పుడు 35-2=33 బాల్స్ ఉన్నాయి. సమాధానం 33.\n'
        '\n'
        'ప్రశ్న: ఒలీవియా వద్ద $23 ఉన్నాయి. ఆమె ఒక్కొక్కటి $3 విలువ చేసే ఐదు గాజులు కొనుగోలు చేసింది. ఆమె వద్ద ఎంత డబ్బు మిగిలి ఉంది?\n'
        'దశలవారీగా సమాధానం: ఒక్కొక్కటి $3 చొప్పున 5 గాజుల ధర 5*3=15 డాలర్లు. ఒలీవియా వద్ద ప్రారంభంలో $23 ఉన్నాయి. అందువల్ల ఇప్పుడు ఆమె వద్ద 23-15=8 డాలర్లు మిగిలి ఉన్నాయి. సమాధానం 8.\n'
        '\n',
    ),
    'th': (
        'โจทย์: ',
        'คำตอบทีละขั้นตอน:',
        'โจทย์: โรเจอร์มีลูกเทนนิส 5 ลูก เขาซื้อลูกเทนนิสเพิ่มอีก 2 กระป๋อง โดยแต่ละกระป๋องมีลูกเทนนิส 3 ลูก ตอนนี้เขามีลูกเทนนิสกี่ลูก\n'
        'คำตอบทีละขั้นตอน: โรเจอร์เริ่มด้วยการมีลูกเทนนิส 5 ลูก กระป๋อง 2 ใบที่มีลูกเทนนิสใบละ 3 ลูก เท่ากับมีลูกเทนนิส 6 ลูก ดังนั้น 5 + 6 = 11 คำตอบคือ 11\n'
        '\n'
        'โจทย์: มีคอมพิวเตอร์เก้าเครื่องในห้องเซิร์ฟเวอร์ โดยตั้งแต่วันจันทร์ถึงวันพฤหัสบดีมีคอมพิวเตอร์ติดตั้งเพิ่มอีกวันละห้าเครื่อง ตอนนี้มีคอมพิวเตอร์ในห้องเซิร์ฟเวอร์กี่เครื่อง\n'
        'คำตอบทีละขั้นตอน: ตั้งแต่วันจันทร์ถึงวันพฤหัสบดีรวมกันเป็น 4 วัน โดยแต่ละวันเพิ่มคอมพิวเตอร์ไป 5 เครื่อง แสดงว่าเพิ่มคอมพิวเตอร์ไปทั้งหมด 4 * 5 = 20 เครื่อง แรกเริ่มมีคอมพิวเตอร์อยู่ 9 เครื่อง ดังนั้น ตอนนี้จะมีคอมพิวเตอร์อยู่ 9 + 20 = 29 เครื่อง คำตอบคือ 29\n'
        '\n'
        'โจทย์: ลีอามีช็อกโกแลตอยู่ 32 ชิ้น และน้องสาวมีช็อกโกแลตอยู่ 42 ชิ้น หากทั้งสองคนทานช็อกโกแลตไปแล้ว 35 ชิ้น จะเหลือช็อกโกแลตทั้งหมดกี่ชิ้น\n'
        'คำตอบทีละขั้นตอน: ลีอามีช็อกโกแลตอยู่ 32 ชิ้น และน้องสาวมีช็อกโกแลตอยู่ 42 ชิ้น แสดงว่าเดิมมีช็อกโกแลตอยู่ 32 + 42 = 74 ชิ้น หากทานไปแล้ว 35 ชิ้น ดังนั้นจะเหลือช็อกโกแลตทั้งหมดอยู่ 74 - 35 = 39 ชิ้น คำตอบคือ 39\n'
        '\n'
        'โจทย์: ชอว์นมีของเล่นห้าชิ้น ในวันคริสต์มาส เขาได้รับของเล่นจากแม่และพ่อคนละสองชิ้น ตอนนี้ชอว์นมีของเล่นกี่ชิ้น\n'
        'คำตอบทีละขั้นตอน: ชอว์นมีของเล่น 5 ชิ้น เขาได้รับของเล่นจากแม่ 2 ชิ้น แสดงว่าตอนนี้ชอว์นมีของเล่นอยู่ 5 + 2 = 7 ชิ้น แล้วเขาก็ได้รับของเล่นจากพ่อเพิ่มอีก 2 ชิ้น ดังนั้น ชอว์นจึงมีของเล่นรวมทั้งหมด 7 + 2 = 9 ชิ้น คำตอบคือ 9\n'
        '\n'
        'โจทย์: ไมเคิลมีลูกกอล์ฟ 58 ลูก ในวันอังคาร เขาทำลูกกอล์ฟหายไป 23 ลูก, ในวันพุธ เขาทำหายอีก 2 ลูก, สิ้นสุดวันพุธ ไมเคิลมีลูกกอล์ฟกี่ลูก\n'
        'คำตอบทีละขั้นตอน: แรกเริ่ม ไมเคิลมีลูกกอล์ฟอยู่ 58 ลูกและทำหายไป 23 ลูก แสดงว่าเขาเหลือลูกกอล์ฟอยู่ 58 - 23 = 35 ลูก หลังจากนั้นเขาทำหายอีก 2 ลูก ดังนั้น ตอนนี้เขาจึงมีลูกกอล์ฟอยู่ 35 - 2 = 33 ลูก คำตอบคือ 33\n'
        '\n'
        'โจทย์: โอลิเวียมีเงินอยู่ $23 เธอซื้อขนมปังเบเกิลไปห้าชิ้น ราคาชิ้นละ $3 โอลิเวียเหลือเงินอยู่เท่าไร\n'
        'คำตอบทีละขั้นตอน: ขนมปังเบเกิล 5 ชิ้น ราคาชิ้นละ $3 รวมเป็นเงิน 5 * 3 = 15 ดอลลาร์ แรกเริ่มโอลิเวียมีเงินอยู่ $23 ดังนั้น ตอนนี้โอลิเวียจะเหลือเงินอยู่ 23 - 15 = 8 ดอลลาร์ คำตอบคือ 8\n'
        '\n',
    ),
    'zh': (
        '问题：',
        '逐步解答：',
        '问题：罗杰有 5 个网球。他又买了 2 罐网球。每罐有 3 个网球。他现在有多少个网球？\n'
        '逐步解答：罗杰一开始有 5 个球。2 罐各 3 个网球就是 6 个网球。5 + 6 = 11。答案是 11。\n'
        '\n'
        '问题：服务器机房里有九台电脑。从周一到周四，每天又安装了五台电脑。服务器机房里现在有多少台电脑？\n'
        '逐步解答：从周一到周四有 4 天。每天增加 5 台电脑。这意味着一共增加了 4 * 5 = 20 台电脑。一开始有 9 台电脑，所以现在有 9 + 20 = 29 台电脑。答案是 29。\n'
        '\n'
        '问题：利亚有 32 块巧克力，她妹妹有 42 块。如果她们吃了 35 块，她们一共还剩下多少块？\n'
        '逐步解答：利亚有 32 块巧克力，利亚的妹妹有 42 块。这意味着原来有 32 + 42 = 74 块巧克力。35 块被吃掉了。所以她们一共还有 74 - 35 = 39 块巧克力。答案是 39。\n'
        '\n'
        '问题：肖恩有五个玩具。圣诞节他从他爸爸妈妈那里各得到了两个玩具。他现在有多少个玩具？\n'
        '逐步解答：他有 5 个玩具。他从妈妈那里得到 2 个，所以之后他有 5 + 2 = 7 个玩具。然后他又从爸爸那里得到了 2 个，所以他一共有 7 + 2 = 9 个玩具。答案是 9。\n'
        '\n'
        '问题：迈克尔有 58 个高尔夫球。周二，他丢失了 23 个高尔夫球。周三，他又丢失了 2 个。周三结束时他有多少个高尔夫球？\n'
        '逐步解答：迈克尔一开始有 58 个高尔夫球，丢失了 23 个，所以他有 58 - 23 = 35 个。在他又丢失了 2 个后，他现在有 35 - 2 = 33 个球。答案是 33。\n'
        '\n'
        '问题：奥利维亚有 23 美元。她买了五个单价 3 美元的百吉饼。她还剩多少钱？\n'
        '逐步解答：5 个单价 3 美元的百吉饼应该花费 5 * 3 = 15 美元。奥利维亚一开始有 23 美元，所以现在她还剩 23 - 15 = 8 美元。答案是 8。\n'
        '\n',
    ),
}
