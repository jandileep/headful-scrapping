import json
from PIL import Image
from google import genai
from google.genai import types

import os

API_KEY = "AIzaSyCj44Atup-1FRrlGXH5zxQ_pA7QduuhyEc"
INPUT_JSON_FILE_PATH = "/root/headful-scrapping/Food_and_Culture/Cuisines_of_India/Central/The_Food_of_Maharashtra/output_content.json"
OUTPUT_JSON_FILE_PATH = "gemini_culture_questions.json"
MODEL_NAME = "gemini-2.5-flash-preview-05-20" 
BASE_PATH="/root/headful-scrapping/"


FULL_TEXT_CONTENT = """
[
    "# The Food of Maharashtra: A Sweet and Tangy Journey",
    "A Maharashtrian woman, by Raja Ravi Varma",
    "The expression “Indian food” always invokes a riot of flavours arising out of the incredible diversity of the country’s landscape, climate and cultures. The culinary culture of Maharashtra can be best explained from a similar perspective. The landscape of this state presents a patchwork of food habits ranging from the briny flavours of the coastal areas to the rustic flavours of the inner mainland. Apart from certain signature dishes that have found a place in restaurant menus throughout the country (such asVadaPavandPav Bhaji), traditional Maharashtrian food is relatively unknown beyond the confines of the state. Maharashtrian cuisine is one of the most wholesome and underrated cuisines of the Indian subcontinent.",
    "Let us proceed by elaborating further upon the regional diversities of Maharashtra. The territory of Maharashtra can be divided into the following regional formations: Konkan, Desh, Khandesh, Marathwada and Vidarbha. The climatic and cultural peculiarities of every region are reflected in the ingredients and tenor of its food. The Konkan region is the coastal belt of Maharashtra and comprises primarily of the districts and cities of Raigad, Sindhudurg, Ratnagiri, Mumbai and Thane. As is true for most coastal areas, rice and fish are the staples of this region. A specialty of this cuisine is saltwater fishes dipped in a variety of sour-sweet gravies that pair beautifully with steamed rice. Konkani cuisine itself is quite diverse and includes several-sub cuisines such as Malvani and Saraswat Brahmin. Moving inwards from Konkan, one reaches the region known as Desh that includes the main districts of Pune, Satara and Kolhapur. This region historically formed the centre of the Maratha empire. The spicy Kolhapuri cuisine of this region offers a peek into the eating habits of the royals.",
    "Street-food of Maharashtra",
    "Towards the north of Desh is the Khandesh region comprising chiefly of the districts of Nashik, Jalgaon and Ahmednagar. The food of this region reflects culinary influences from neighbouring states such as Rajasthan and Gujarat. For example, items such asDal Baati(Rajasthan) andShev(Gujarat) find a place in the menu of the region. As the area is often visited by drought, hardy crops such asjowarandbajrathrive here. Moving further inland, one comes across the sun-kissed land of Marathwada. This is a hot and arid region where the custom of sun-drying vegetables is quite common. This region includes the districts of Nanded, Beed, Latur, Jalna, Aurangabad and the surrounding areas. To the north of Marathwada lies the Vidarbha region which forms the north-eastern boundary of the state of Maharashtra. This region which includes the districts of Nagpur, Amravati, Chandrapur, Akola and Bhandara, is rich in forest and mineral resources. Although a part of the Maharashtra state, this region has a distinct culture assimilating influences from the neighbouring states of Madhya Pradesh, Chattisgarh and Telangana. Crops such asjowar, bajraandtoorform the staples of the region. A specialised culinary tradition of this region is the Saoji which also bears the influence of Gujarati and Marwari cuisines.",
    "A map of the administrative divisions of Maharashtra",
    "A Maharashtrianthali",
    "However, it is similarities rather than differences that impart the Maharashtrian cuisine a distinct flavour of its own. In Marathi culture, food is considered equivalent to God –“anna he poornabrahma.”A typical MaharashtrianPhodnior tempering (using ghee and select spices) is bound to tantalize the olfactory senses of a MarathiManusirrespective of regional affiliation. Food, in this culinary culture, is mostly sautéed, stir-fried or slow-cooked under pressure. Fish is shallow-fried and meats stewed until succulent.Vaafavneor steaming is a technique used frequently before items are fried. Cereals such asjowar and bajra, and pulses liketoorand Bengal gram are the staples throughout the state, except for the coastal areas where rice is more prevalent. Another defining characteristic of Maharashtrian cuisine is a distinct sweet and sour flavour. Traditionally, jaggery orpuranis the favoured sweetener, although sugar is used in equal measure nowadays. A tropical fruit calledkokumis used as a souring agent (primarily in the coastal regions) for dishes and imparts a unique pink or purple colour to the food. Another commonly used souring agent is tamarind. A ubiquitous ingredient is coconut, used either in fresh or dried/ powdered form. Peanuts too are added to a wide variety of dishes and form the base for various delectable chutneys. Peanut oil is also used for cooking in the region. The traditional way of setting a platter is known asTaat Vadhanyin which all the dishes and accompaniments of athali(platter) are arranged in a particular order. While salt is placed at the top-centre of theTaat(plate), the dessert occupies the left side of the base. To the left of the salt are served accompaniments to the main meal such as a lemon wedge,chatni, salad etc., and to its right are served the vegetables and the main course or curry, followed bypapad and bhakris. Rice is always served in an evenly shaped mound, garnished with ghee.",
    "One of the most beloved and homely dishes of the state isAmti- a Maharashtrian rendering of the commondaal. This variety of daal is made out oftoor. The use ofkokumor tamarind, coconut and jaggery provide this dish with its characteristic sweet, tangy and spicy flavour. However, the most important ingredient is theGodamasala - a unique blend of spices including cumin, cinnamon, pepper, coriander,ajwain, cloves and sesame (to name a few). Another popular dish, which is as much a part of the regular household menu as of feasts and special occasions, isBharli Vangi. The dish is prepared by stuffing raw eggplant with a lip-smacking mixture of coconut, peanuts,Goda masala, tamarind and onions. The stuffed eggplants are cooked until they absorb the flavour of the spices and attain a soft texture. The dish is best enjoyed withbhakrisor flatbreads made (most commonly) out ofjowar, bajraand (sometimes) wheat.",
    "Usal",
    "Bharli Vangdi",
    "Maharashtrian food is nutrient-rich and prepared in a manner to preserve the goodness of the ingredients. An example of such a wholesome dish isUsalwhich is prepared with a variety of sprouted beans or legumes such as moong beans, green peas and black gram. The legumes are steamed under pressure and tomatoes, coconut, onions, ginger and garlic are added to it. This curried dish pairs incredibly well with softbhakrisandpavs(bread). TomatoSaaris a mild and soothing soup of tomatoes, coconut and spices. Another quintessential comfort dish isMetkut Bhat.Metkutis a powder prepared out of lentils, grains and spices and is found on the shelves of most Marathi households.Metkutwith rice orkhichdi, tempered by a dollop of ghee is the perfect remedy for the ailing body as well as the soul.",
    "Maharashtrian cuisine has an incredible variety of snacks that have won hearts and bellies both within the region and beyond.Pav BhajiandVada Pavare two dishes that rule the realm of fast foods.Pav Bhajiinvolves a mix of vegetables cooked in butter and a special blend of spices, accompanied by apav. A walk along the beaches of Mumbai would probably be incomplete without aVada Pav, a popular street food of the city. It is essentially a deep-friedbatataor potato dumpling placed inside apavsplit in the middle.Misal Pavis a spicy curry made of sprouted beans topped with chopped onions, cilantro,farsanand a dash of lime, accompanied by apav. Another quick yet wholesome dish isPithla, known as the quintessential peasant’s meal, but has lately gained immense popularity among city-dwellers.Pithlais a quick dish whisked out of gram flour, onion, ginger, garlic and spices and eaten with softbhakris.Poha, a dish that finds a place on the breakfast table almost all over the country today, is said to be of Maharashtrian origin.Pohais flattened rice mixed with a tempering of oil, curry leaves, onions, mustard seeds and peanuts.",
    "The onset of monsoons in Maharashtra brings its own basket of savoury snacks.Alu Vadiis one such beloved snack made of collocasia leaves smeared inbesanor gram flour, and then steamed and fried to reach the right amount of crispness.Sabudana Vadiare crisp patties made out ofsabudana(tapioca sago), potato and peanuts, and often eaten as a fasting snack. Another popular fasting snack isSabudana Khichdiin which thesabudanais tossed in oil with potatoes, peanuts and herbs.Hurda bhelis a popular winter snack that is prepared out of tenderjowargrains mixed with butter, tomato, onions,shevand peanut chutney.",
    "Any discussion on a region’s cuisine is incomplete without a look at its royal fare. In Maharashtra, the Kolhapuri cuisine with its rich non-vegetarian dishes and spicyrassas(gravies) acquaint us with the flavours of the royal Marathi kitchens. Kolhapur was a princely state ruled by the Bhonsle dynasty that merged with the Indian union in 1949. Meat, mostly mutton, forms an important part of the Kolhapuri meal. Traditionally,shikaror game meat such as vension, wild boar and partridge also formed a part of the royal menu (before hunting was declared illegal). The characteristic spiciness and boldness of Kolhapuri dishes comes from a unique blend of spices known askanda-lasunmasala.",
    "Tambda Rassa & Pandhra Rassa",
    "Kolhapuri Mutton",
    "An unusually fiery variant of chilli known aslavangi mirch, native to this region, is bound to flare up one’s senses.Mutton Sukkais a spicy delicacy prepared by cooking meat in grated coconut and a blend of choice spices. Two delectable Kolhapuri curries crafted to tease one’s taste buds areTambda Rassa and Pandhra Rassa, literally translated as red and white curries. While red chillies are the star component of theTambda Rassaimparting its fiery red colour, grated coconut paste lends a smooth and creamy consistency to thePandhra Rassa.",
    "It is interesting to note that one of the earliest printed Marathi cookbooks,Rasachandrika, was published in 1943 by the Saraswat Mahila Samaj. This text, authored by Ambabai Samsi, features classic recipes of the Saraswat community. While predominantly vegetarian, fish finds a place in the culinary repertoire of this community as it is euphemistically treated as the vegetable of the sea. Another specialised cuisine of Maharashtra is the Saoji, native to the Nagpur region. Saoji style of cooking is practiced by the Halba Koshti community, who were traditionally weavers. The cuisine involves spicy mutton and chicken curries that carry a characteristic flavour. This distinctiveness emerges out of a special blend of spices the ingredients of which are a closely guarded secret within the community.",
    "Scrumptious desserts are the markers of a versatile cuisine. Maharashtrian desserts are as wholesome and mouth-watering as its snacks and main dishes. One of the most popular and celebrated desserts of Maharashtra isPuran Poliwhich is essentially a flatbread(poli)stuffed with Bengal gram powder and jaggery(puran), served with a dollop of ghee.Shrikhandis another dessert of Maharashtrian origin in which hung curd, powdered sugar, and a flavour of choice (elaichi, kesaror mango) is whipped to reach a creamy and silky consistency.",
    "Shrikhand",
    "Puran Poli",
    "Another delectable dairy-based dessert isBasundiwhich is prepared by boiling milk over a low flame till it thickens. Thereafter cardamom, nutmeg and dry-fruits are added to it. A discussion of Maharashtrian desserts is incomplete without theUkadiche Modak, the favoured delicacy of Lord Ganesha. These are steamed dumplings of rice flour skin stuffed with a mixture of coconut and jaggery.Modaksare served asbhoga or prasadaduring Ganesh Chaturthi, one of the most popular festivals of Maharashtra.",
    "Modaks"
]
"""

try:
    client= genai.Client(api_key=API_KEY)
except Exception as e:
    print(f"Error configuring GenAI: {e}")
    print("Please ensure your API_KEY is correctly set.")
    exit()

try:
    with open(INPUT_JSON_FILE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    images_info = data.get("images", [])
    if not images_info:
        print(f"No 'images' array found in {INPUT_JSON_FILE_PATH} or it is empty.")
        exit()
except FileNotFoundError:
    print(f"Error: The file {INPUT_JSON_FILE_PATH} was not found.")
    exit()
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from {INPUT_JSON_FILE_PATH}.")
    exit()
except Exception as e:
    print(f"An unexpected error occurred while loading JSON: {e}")
    exit()




all_results = []

for image_detail in images_info:
    relative_local_path = image_detail.get("local_path") # Path from JSON
    original_caption = image_detail.get("caption", "No caption provided.")

    if not relative_local_path:
        print(f"Skipping entry due to missing 'local_path': {image_detail}")
        continue


    full_image_path = os.path.join(BASE_PATH, relative_local_path)
    
    image_filename = os.path.basename(relative_local_path) 

    if not os.path.exists(full_image_path):
        print(f"Image file not found at: {full_image_path}. Skipping {image_filename}.")
        all_results.append({
            "image_name": image_filename,
            "original_caption": original_caption,
            "gemini_response": f"Error: Image file not found at {full_image_path}."
        })
        continue

    print(f"\n--- Processing image: {image_filename} ---")
    print(f"Full path: {full_image_path}") 
    print(f"Using original caption: {original_caption}")

    image_opened = None
    try:
        image_opened = Image.open(full_image_path)

        prompt_template = f"""You are an AI assistant specialized in crafting **exceptionally challenging and profoundly culture-specific questions** for a multimodal benchmark heavily focused on **Indian culture**. Your objective is to generate questions that rigorously test a deep, nuanced understanding and synthesis of information from visual and textual sources. **The images provided will depict a distinct cultural concept from Indian culture (e.g., a specific practice, unique tradition, specialized food, symbolic clothing, significant artifact, or intricate event), and the accompanying text (Image Caption and Full Text) will provide intricate details and context about these unique cultural aspects.**

**General Guiding Principles (Applicable to all questions):**

* **Ultimate Goal:** To create questions that assess a profound and nuanced understanding of the specific Indian cultural elements detailed in the provided Image, Caption, and Full Text. Questions must be challenging enough that they **cannot be answered through superficial understanding, general knowledge of 'Indian culture,' or common sense, but absolutely require specific, deep insights gained *only* from the provided materials.**
* **No Stereotypes:** All questions must be based on factual, specific information as presented in the provided materials and rigorously avoid perpetuating cultural stereotypes or over-simplified beliefs. Focus on authentic, detailed cultural representations.
* **Culturally Precise Terminology:**
    * For universal concepts, use standard English terms.
    * For culturally specific Indian concepts, answers and relevant multiple-choice options must use the widely recognized and agreed-upon local Indian name, as potentially referenced or implied by the text and visually identifiable. (e.g., "Naan," "Sari," "Pooja," "Mantapa").

You will be provided with the following three components for each item:

1.  **Image:** (The image is provided as a separate input to you)
2.  **Image Caption:** A brief description, title, or relevant information accompanying the image.
3.  **Full Text:** A more extensive piece of text that provides specialized details and context about the Indian cultural aspects related to the image and caption.

---
**Task 1: Exceptionally Challenging Multimodal Comprehension Questions (Image + Caption + Full Text)**

Your task is to formulate **1-2 Multiple Choice Questions (MCQs) AND 1-2 Subjective Questions** in English. These questions must integrate information from **all three sources: the Image, the Image Caption, and the Full Text**, demanding a sophisticated synthesis.

**Key Guidelines for Task 1:**

1.  **Indispensability of Image:** All questions **must be fundamentally unanswerable without meticulous observation and critical interpretation of the Image.** The visual details from the image, when combined with textual information, must be crucial for unlocking the answer. The synthesis required should be non-obvious.
2.  **Implicit Text Reliance (No Explicit References):** When formulating questions, **do not use phrases like 'According to the text,' or similar explicit references.** The questions must inherently demand expert knowledge *from the provided Full Text* for a correct answer, with this reliance being implicit.
3.  **Profound Cultural Depth & Specificity:**
    * Questions must be **profoundly culture-specific**, focusing on unique Indian cultural concepts, practices, symbolism, or nuanced interpretations as detailed in the **Full Text** and **Image Caption**, and as manifested or contextualized by the **Image**.
    * These questions must be designed to be **virtually unanswerable without a meticulous synthesis and deep understanding of the specific cultural details presented across all provided materials.** They should act as a filter for superficial comprehension.
4.  **Extreme Complexity & Higher-Order Thinking:**
    * Demand more than simple recall or direct matching. Questions should require **multi-step reasoning, identification of subtle cultural markers (both visual and textual) and their explained significance, understanding of implicit cultural assumptions or values presented in the text and their visual manifestations, and advanced analytical or inferential leaps.**
5.  **Precision & Unambiguity:** Despite their difficulty, questions must be clear, unambiguous, and meticulously worded to point towards a single best answer derivable from a deep and combined interpretation of the image, caption, and full text.

**Formatting for Task 1 Questions:**

* **For MCQ Questions:**
    * `Question: [English Question Text]`
    * `Answer: [Correct Option Letter, e.g., A]`
    * `Options:`
        * `A) [Correct Option Text using appropriate terminology]`
        * `B) [Distractor 1 Text]`
        * `C) [Distractor 2 Text]`
        * `D) [Distractor 3 Text]`
        *(Distractors must be highly plausible, potentially representing common misconceptions, related but distinct cultural concepts not covered in *this specific text*, or interpretations that would seem valid without the full, deep understanding of all provided materials. They must be as challenging as the question itself.)*

* **For Subjective Questions:**
    * `Question: [English Question Text]`
    * `Answer: [Brief Phrase Answer using appropriate terminology. Not a full sentence. E.g., "ritualistic purification," "ancestral offering," "marriage proposal symbol"]`

---
**Task 2: Expert-Level Textual Comprehension Questions (Full Text-Only)**

Your task is to formulate **1-2 Multiple Choice Questions (MCQs) AND 1-2 Subjective Questions** in English, based **solely on the provided Full Text.** The image and caption are irrelevant for this task.

**Key Guidelines for Task 2:**

1.  **Strictly Text-Only Basis:** Answers must be derivable exclusively from the nuanced information and complex concepts presented in the **Full Text**.
2.  **Implicit Text Reliance (No Explicit References):** When formulating questions, **do not use phrases like 'According to the text,' or similar explicit references.** The questions must inherently demand expert knowledge *from the provided Full Text* for a correct answer, with this reliance being implicit.
3.  **Intense Focus on Unique Cultural Nuances:**
    * Questions must be **intensely focused on unique and non-obvious cultural nuances, underlying beliefs, specific terminologies with deep cultural resonance (as defined in the text), intricate social dynamics, complex symbolic interpretations, or philosophical underpinnings presented in the Full Text.**
4.  **Expert-Level Complexity and Critical Thinking:**
    * Questions should demand **expert-level comprehension of the text, going far beyond surface meaning to explore implicit relationships, unstated assumptions based on textual clues, the significance of details that might seem minor to a non-expert reader but are loaded with cultural meaning according to the text, or require synthesizing disparate pieces of complex cultural information from the text.**
5.  **Critical Filter: Unanswerable Without Deep Textual Cultural Knowledge:**
    * **This is a paramount directive.** Design questions such that an individual, even if generally knowledgeable or intelligent, would be **unable to deduce or infer the correct answer without having thoroughly comprehended and internalized the specific, often subtle, cultural information, definitions, and context provided *exclusively within the Full Text*.** The questions must serve as a robust test of this deep and specific textual understanding.
6.  **Precision & Unambiguity:** Despite their advanced difficulty, questions must be precisely worded to ensure a single, best answer is clearly supported by a deep analysis of the text.

**Formatting for Task 2 Questions:**

* **For MCQ Questions:**
    * `Question: [English Question Text - without explicit text reference]`
    * `Answer: [Correct Option Letter, e.g., A]`
    * `Options:`
        * `A) [Correct Option Text using appropriate terminology from text]`
        * `B) [Distractor 1 Text]`
        * `C) [Distractor 2 Text]`
        * `D) [Distractor 3 Text]`
        *(Distractors must be extremely plausible, perhaps reflecting sophisticated misinterpretations or closely related concepts that require expert textual knowledge to differentiate.)*

* **For Subjective Questions:**
    * `Question: [English Question Text - without explicit text reference]`
    * `Answer: [Brief Phrase Answer using appropriate terminology from text. Not a full sentence. E.g., "karmic consequence," "ritual purity maintenance," "lineage honor"]`

---

**Instructions for AI Model receiving this prompt:**
* Thoroughly internalize all general guiding principles, especially the emphasis on extreme difficulty and dependence on the provided materials.
* For Task 1, generate the specified number of MCQ and Subjective multimodal questions that are exceptionally challenging.
* For Task 2, generate the specified number of MCQ and Subjective text-only questions that demand expert-level comprehension of the text's cultural nuances, ensuring no explicit text references.
* All answers and options must strictly adhere to the culturally precise terminology and brief phrase format for subjective answers.
* The primary goal is to create questions that are **unanswerable by those lacking deep, specific knowledge derived *only* from the provided materials.**

**Now, analyze the following inputs and generate your questions as per Task 1 and Task 2:**

**Image Caption:**
[{original_caption}]

**Full Text:**
{FULL_TEXT_CONTENT}
"""
        print(f"Sending to Gemini for {image_filename}...")
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[image_opened, prompt_template],
            config=types.GenerateContentConfig(
                # You can add temperature, top_p etc. if needed
                # temperature=0.7 
            ),
            # safety_settings can be adjusted if needed, e.g. to be less restrictive
            # safety_settings={'HARASSMENT':'block_none'}
        )

        gemini_response_text = ""
        if response and hasattr(response, 'text'):
            gemini_response_text = response.text
            print("Gemini Response Received.")
        elif response and response.parts:
            gemini_response_text = " ".join(part.text for part in response.parts if hasattr(part, 'text'))
            print("Gemini Response (from parts) Received.")
        else:
            block_reason = "Unknown"
            safety_ratings_str = "Not available"
            if response.prompt_feedback:
                block_reason = response.prompt_feedback.block_reason
                safety_ratings_str = str(response.prompt_feedback.safety_ratings)
            
            gemini_response_text = f"Error: No text in response. Block reason: {block_reason}. Safety Ratings: {safety_ratings_str}"
            print(gemini_response_text)
            if response.candidates and not response.candidates[0].content.parts:
                 print(f"Finish reason for empty candidate: {response.candidates[0].finish_reason}")


        all_results.append({
            "image_name": image_filename,
            "original_caption": original_caption,
            "gemini_response": gemini_response_text
        })

    except FileNotFoundError:
        error_message = f"Error: Image file not found at {local_path} (double check after os.path.exists)."
        print(error_message)
        all_results.append({
            "image_name": image_filename,
            "original_caption": original_caption,
            "gemini_response": error_message
        })
    except Image.UnidentifiedImageError:
        error_message = f"Error: Cannot identify image file. It might be corrupted or not a valid image: {local_path}"
        print(error_message)
        all_results.append({
            "image_name": image_filename,
            "original_caption": original_caption,
            "gemini_response": error_message
        })
    except Exception as e:
        error_message = f"An error occurred while processing {image_filename}: {e}"
        print(error_message)
        all_results.append({
            "image_name": image_filename,
            "original_caption": original_caption,
            "gemini_response": error_message
        })
    finally:
        if image_opened:
            image_opened.close()

    print("--------------------------------------")

try:
    with open(OUTPUT_JSON_FILE_PATH, 'w', encoding='utf-8') as outfile:
        json.dump(all_results, outfile, indent=4, ensure_ascii=False)
    print(f"\nSuccessfully saved all responses to {OUTPUT_JSON_FILE_PATH}")
except IOError:
    print(f"Error: Could not write results to {OUTPUT_JSON_FILE_PATH}.")
except Exception as e:
    print(f"An unexpected error occurred while saving JSON: {e}")

print("\nScript finished.")