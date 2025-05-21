from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch
import torch.nn.functional as F

def load_model():
    """
    Load the pre-trained NER model and tokenizer.
    Returns:
        tuple: (tokenizer, model)
    """
    print("Loading NER model and tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
    model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")
    print("NER model and tokenizer loaded successfully")
    return tokenizer, model

# Load the model and tokenizer
tokenizer, model = load_model()

def tokenize_text(text):
    """
    Tokenize the input text for NER processing.
    
    Args:
        text (str): Raw text to tokenize
        
    Returns:
        dict: Dictionary with input_ids and attention_mask tensors
    """
    return tokenizer(text, return_tensors="pt", truncation=True, padding=True)

def predict_entities(text):
    """
    Predict named entities in the given text with confidence scores.
    
    Args:
        text (str): Raw text to analyze
        
    Returns:
        list: List of (token, tag, confidence) tuples
    """
    inputs = tokenize_text(text)
    with torch.no_grad():
        outputs = model(**inputs).logits
    
    # Apply softmax to get probabilities
    probs = F.softmax(outputs, dim=2)
    
    # Get the highest probability and its index
    max_probs, predictions = torch.max(probs, dim=2)
    
    # Get the tokens and their predicted tags
    token_ids = inputs["input_ids"][0]
    tokens = tokenizer.convert_ids_to_tokens(token_ids)
    tags = [model.config.id2label[p.item()] for p in predictions[0]]
    confidences = [prob.item() for prob in max_probs[0]]
    
    # Filter out special tokens like [CLS], [SEP], [PAD]
    entity_pairs = []
    for token, tag, confidence in zip(tokens, tags, confidences):
        if token.startswith("##"):  # Handle wordpiece tokenization
            if entity_pairs:
                # Merge with previous token if it exists
                prev_token, prev_tag, prev_conf = entity_pairs[-1]
                # Average the confidences
                avg_conf = (prev_conf + confidence) / 2
                entity_pairs[-1] = (prev_token + token[2:], prev_tag, avg_conf)
        elif not (token == "[CLS]" or token == "[SEP]" or token == "[PAD]"):
            entity_pairs.append((token, tag, confidence))
    
    return entity_pairs

def group_entities(entity_pairs):
    """
    Group consecutive tokens with the same entity type and calculate average confidence.
    
    Args:
        entity_pairs (list): List of (token, tag, confidence) pairs
        
    Returns:
        list: List of (entity_text, entity_type, confidence) triplets
    """
    grouped_entities = []
    current_entity = []
    current_confidences = []
    current_type = "O"
    
    for item in entity_pairs:
        token, tag = item[0], item[1]
        confidence = item[2] if len(item) > 2 else 1.0  # Default confidence if not provided
        
        # Extract the entity type without B- or I- prefix
        if tag != "O":
            entity_type = tag[2:] if tag.startswith("B-") or tag.startswith("I-") else tag
        else:
            entity_type = "O"
        
        # Check if we're starting a new entity or continuing the current one
        if tag.startswith("B-"):  # Beginning of a new entity
            if current_entity:  # Save the previous entity if it exists
                avg_confidence = sum(current_confidences) / len(current_confidences)
                grouped_entities.append((" ".join(current_entity), current_type, avg_confidence))
                current_entity = []
                current_confidences = []
            current_entity.append(token)
            current_confidences.append(confidence)
            current_type = entity_type
        elif tag.startswith("I-") and current_type == entity_type:  # Inside the current entity
            current_entity.append(token)
            current_confidences.append(confidence)
        elif tag == "O":  # Outside any entity
            if current_entity:  # Save the previous entity if it exists
                avg_confidence = sum(current_confidences) / len(current_confidences)
                grouped_entities.append((" ".join(current_entity), current_type, avg_confidence))
                current_entity = []
                current_confidences = []
                current_type = "O"
        else:  # Tag is different from current entity or doesn't follow expected pattern
            if current_entity:  # Save the previous entity if it exists
                avg_confidence = sum(current_confidences) / len(current_confidences)
                grouped_entities.append((" ".join(current_entity), current_type, avg_confidence))
                current_entity = []
                current_confidences = []
            if tag != "O":  # Start a new entity if the tag is not O
                current_entity.append(token)
                current_confidences.append(confidence)
                current_type = entity_type
    
    # Don't forget the last entity if there is one
    if current_entity:
        avg_confidence = sum(current_confidences) / len(current_confidences)
        grouped_entities.append((" ".join(current_entity), current_type, avg_confidence))
    
    return grouped_entities 