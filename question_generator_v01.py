import random
import pickle

with open('./pkl_files/AutoTokenizer.pkl', 'rb') as file:
    tokenizer = pickle.load(file)
with open('./pkl_files/AutoModelForSeq2SeqLM.pkl', 'rb') as file:
    model = pickle.load(file)
actual_answers = []

def generate_random_questions_batch(documents, num_questions):
    questions = []

    for document in documents:
        if len(document.split()) <= 1:
            continue  # Skip empty or very short documents

        text_lengths = [random.randint(1, min(len(document.split()) - 1, 10)) for _ in range(2)]

        start_indices = [random.randint(0, len(document.split()) - text_length - 1) for text_length in text_lengths]

        input_texts = [
            " ".join([
                document.split()[i] if i < start_index or i >= start_index + text_length else "[HL]" 
                for i in range(len(document.split()))
            ]) for start_index, text_length in zip(start_indices, text_lengths)
        ]

        temp_answers = []

        for input_text in input_texts:
            temp = input_text.split()
            while "[HL]" in temp:
                temp.remove("[HL]")
            string = " ".join(temp)
            temp_answers.append(string)

        actual_answers.extend(temp_answers)

        input_ids_list = [tokenizer(input_text, return_tensors="pt").input_ids for input_text in input_texts]

        # Assuming model input limit is 512 tokens, you may need to adjust this based on your model
        max_tokens = 512

        for input_ids in input_ids_list:
            # Split input_ids into chunks of size max_tokens
            for i in range(0, len(input_ids[0]), max_tokens):
                input_ids_chunk = input_ids[:, i:i + max_tokens]

                # Generate output for each chunk
                output = model.generate(input_ids_chunk)

                # Decode the generated output
                generated_question = tokenizer.decode(output[0], skip_special_tokens=True)
                questions.append(generated_question)

    return questions

def questions_generator_driver():
    document = ""
# Split the document into smaller chunks for batch processing
    chunk_size = 300  # You may need to adjust this based on your document size
    document_chunks = [document[i:i + chunk_size] for i in range(0, len(document), chunk_size)]

    num_broader_questions = 3
    num_niche_questions = 2

    broader_questions = generate_random_questions_batch(document_chunks, num_broader_questions)
    broader_final_questions = random.sample(broader_questions, k=5)
    niche_questions = generate_random_questions_batch(document_chunks, num_niche_questions)
    niche_final_questions = random.sample(niche_questions, k=5)
     