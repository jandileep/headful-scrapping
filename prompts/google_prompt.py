from google import genai
from PIL import Image

client = genai.Client(api_key="AIzaSyCj44Atup-1FRrlGXH5zxQ_pA7QduuhyEc")


image = Image.open("/root/headful-scrapping/Food_and_Culture/Cuisines_of_India/Central/The_Food_of_Maharashtra/images/maharashtrian-11_11.jpg")
response = client.models.generate_content_stream(
    model="gemini-2.5-flash-preview-05-20",
    contents=[image, """You are an AI assistant specialized in crafting insightful questions for a multimodal benchmark heavily focused on **Indian culture**. Your objective is to generate a diverse set of questions that effectively test understanding and synthesis of information from visual and textual sources. **The images provided will typically depict a cultural concept from Indian culture (e.g., a practice, tradition, food, clothing, artifact, or event), and the accompanying text will provide details and context about these cultural aspects.**

You will be provided with the following three components for each item:

1.  **Image:** A visual image depicting an aspect of Indian culture.
2.  **Image Caption:** A brief description, title, or relevant information accompanying the image.
3.  **Full Text:** A more extensive piece of text that provides specific details and context about the Indian cultural aspects related to the image and caption.

---
**Task 1: Generating General Multimodal Comprehension Questions**

Based on all three provided components (Image, Image Caption, and Full Text), generate a set of questions designed to assess comprehension at various levels:

* **A. Visual Comprehension (Image-based - General):**
    * Questions answerable by observing the **Image**. Focus on overall scenes, primary subjects, and clear actions or settings relevant to the depicted cultural context.
* **B. Textual Comprehension (Full Text-based):**
    * Questions requiring understanding, recall, or inference of cultural information from the **Full Text**.
* **C. Multimodal Comprehension (Image + Text Integration):**
    * Questions requiring connection, comparison, or synthesis of information from the **Image** with the cultural details in the **Full Text**.

**Guidelines for Task 1 Questions:**

1.  **Diversity:** Varied question types (What, Why, How, Describe, Explain the significance of...).
2.  **Clarity:** Clear, unambiguous questions.
3.  **Relevance:** Answerable using only the provided materials.
4.  **Cultural Depth (Emphasis for Text-based and Multimodal Questions):**
    * Questions, particularly those drawing from the Full Text (C) and multimodal connections (D), must be **heavily culture-related**, focusing on the specific Indian cultural concepts, practices, traditions, significance, and nuances detailed in the provided **Full Text**.
    * These questions should be framed such that they **require a deep understanding of the cultural information presented *in the provided Full Text*.** Ideally, someone who has not carefully read and understood these specific cultural details from the text would find it very difficult or impossible to answer them correctly.
    * The question must aim to test comprehension of the unique cultural information imparted by the text, not general knowledge.
5.  **Precision:** Do not ask questions that are vague, under-specified, or could have multiple correct interpretations, especially when dealing with nuanced cultural information. Ensure one clear answer can be derived from the provided materials.
6.  **Number of Questions:** Aim for 3-5 questions covering these categories for this task.
7.  **Output Format:** A numbered list of questions. (Answers are not required for Task 1 questions unless specified otherwise).

---
**Task 2: Generating In-Depth, Image-Only Questions with Multiple Choice Answers (English Only)**

For the provided **Image** only, your task is to formulate 1-3 complex and culturally relevant questions in English. These questions must adhere strictly to the following guidelines:

1.  **Source of Truth:** The question MUST be answerable *solely* by careful observation of the visual details within the **Image**. No external knowledge or information from the caption or full text should be required to determine the correct answer from the visual information presented. The question must be answerable even *before* seeing the multiple-choice options.
2.  **Question Complexity and Variation:**
    * **Avoid Overly Simple/Direct Questions:** Do not ask basic identification questions like "What is in the image?" The goal is complexity that probes detailed observation of culturally relevant visual elements.
    * **Aim for questions that require:**
        * **Detailed Observation & Referencing of Cultural Elements:** Noticing subtle details in attire, artifacts, symbols, ritualistic arrangements, or specific features of culturally significant items, and their relation to other elements in the image. E.g., "What distinctive motif, visible on the [specific cultural item] held by the central figure, suggests its ceremonial use rather than everyday utility?"
        * **Multi-Hop Visual Reasoning within Cultural Context:** Inferring relationships or activities based on multiple visual cues that together point to a culturally specific scenario depicted. E.g., "Considering the type of [vessel] shown and the [specific plant material] placed beside it, what initial step of a traditional practice is most likely being depicted?"
        * **Complex Counting/Quantification of Cultural Identifiers:** E.g., "How many distinct traditional patterns can be identified on the borders of the textile worn by the figure on the right?"
        * **Visually Grounded Inference about Cultural Aspects:** Drawing conclusions about function, purpose, or context based on visual evidence of cultural items or scenes within the image. E.g., "Based on the specific adornments and the posture of the depicted individual, what type of traditional performance or role is most strongly suggested by the visual evidence in this image?"
3.  **Cultural Relevance, Specificity, and Sensitivity:**
    * Ensure questions are culturally relevant and highly specific to the unique **Indian cultural content** shown in the image. Frame questions that require nuanced observation of visually distinguishable cultural elements.
    * While the answer must be derived *solely from the image*, the *choice* of what to ask about should reflect the benchmark's focus on Indian culture. The questions should aim to uncover an understanding of these visual cultural elements.
    * Frame questions respectfully, being mindful of cultural sensitivities and avoiding stereotypes or misrepresentations.
    * Ensure questions are not vague or under-specified. The visual evidence in the image must clearly support a single correct answer to the question asked.
4.  **Language:**
    * All questions must be in clear and fluent **English**.
    * **Format for questions:**
        * `Question: [English Question Text]`
5.  **Answer and Multiple-Choice Options:**
    * For each question, provide a **Concise Answer** derived directly and accurately from the image.
    * **Culturally Precise Terminology for Answers and Options:**
        * For universal concepts (e.g., common animals, general objects, colors), use standard English terms. (e.g., "dog" not "kutta"; "red"; "plate").
        * For culturally specific Indian concepts depicted in the image (e.g., specific dishes, clothing items, artifacts, ritual elements, traditional practices), the **Answer** and the **Correct Option** must use the widely recognized and agreed-upon local Indian name for that concept, if visually identifiable as such. (e.g., if a specific bread is shown, use "Naan" or "Roti" as appropriate and visually distinguishable, not just "bread"; for a specific garment, use "Sari" or "Kurta" if visually identifiable, not just "dress" or "shirt").
        * This ensures answers reflect common understanding within Indian culture. Distractors should also be mindful of this, using appropriate terminology to remain plausible.
    * **Format for answer and options:**
        * `Answer: [Concise Answer Text using appropriate terminology]`
        * `Options:`
            * `A) [Correct Option Text using appropriate terminology]`
            * `B) [Distractor 1 Text, mindful of terminology]`
            * `C) [Distractor 2 Text, mindful of terminology]`
            * `D) [Distractor 3 Text, mindful of terminology]`
6.  **Number of Image-Only Questions:** Generate 1-3 complete sets (Question + Answer + MCQs) per image for this Task 2.

---

**Instructions for AI Model receiving this prompt:**
* First, address Task 1 using the Image, Image Caption, and Full Text, paying close attention to the cultural depth required for text-based and multimodal questions.
* Then, address Task 2 using ONLY the Image, focusing on complex visual analysis of culturally relevant elements and using culturally precise terminology for answers and options.
* Ensure all guidelines for each task are meticulously followed.

**Now, analyze the following inputs and generate your questions as per Task 1 and Task 2:**



**Image Caption:**
[Kolhapuri Mutton]

**Full Text:**
[        "# The Food of Maharashtra: A Sweet and Tangy Journey",
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
        "Modaks"]"""]
)
for chunk in response:
    print(chunk.text, end="")