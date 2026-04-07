"""
Scenario bank for ModelJury-Env.
All ground truths are pre-defined — graders are 100% deterministic.
"""

HALLUCINATION_SCENARIOS = [
    {
        "id": "hall_001",
        "question": "Who invented the telephone and in what year was the first patent granted?",
        "responses": [
            "Alexander Graham Bell invented the telephone. He received the first US patent for it on March 7, 1876, beating Elisha Gray by just a few hours.",
            "The telephone was invented by Alexander Graham Bell in 1869. He demonstrated it at the Philadelphia Centennial Exposition and made the first call to his assistant Thomas Watson.",
            "Alexander Graham Bell is credited with inventing the telephone. He filed his patent in 1876 and the device was publicly showcased at the 1876 Philadelphia Centennial Exposition.",
        ],
        "hallucinated_index": 1,
        "error_keywords": ["1869", "wrong year", "incorrect year", "1876", "date", "year"],
    },
    {
        "id": "hall_002",
        "question": "What is the boiling point of water at sea level in Celsius?",
        "responses": [
            "Water boils at 100 degrees Celsius (212 degrees Fahrenheit) at sea level, where atmospheric pressure is 1 atm.",
            "Water boils at 100 degrees Celsius at sea level. At higher altitudes like Denver, water boils at approximately 95 degrees Celsius due to lower atmospheric pressure.",
            "Water boils at 90 degrees Celsius at standard sea-level pressure of 1 atmosphere. This is one of the key calibration points on the Celsius scale.",
        ],
        "hallucinated_index": 2,
        "error_keywords": ["90", "wrong temperature", "100", "incorrect", "celsius"],
    },
    {
        "id": "hall_003",
        "question": "How many planets are in our solar system, and who made the official reclassification of Pluto?",
        "responses": [
            "There are 8 planets in our solar system. In 2006, the International Astronomical Union reclassified Pluto as a dwarf planet.",
            "Our solar system has 9 planets including Pluto, which was officially demoted to dwarf planet status by NASA in 2006.",
            "There are 8 planets. The IAU voted in 2006 to reclassify Pluto as a dwarf planet.",
        ],
        "hallucinated_index": 1,
        "error_keywords": ["nasa", "iau", "international astronomical union", "wrong organization", "9 planets"],
    },
    {
        "id": "hall_004",
        "question": "What is Python's Global Interpreter Lock (GIL)?",
        "responses": [
            "The GIL is a mutex in CPython that prevents multiple native threads from executing Python bytecode simultaneously. It has existed since the earliest CPython versions.",
            "The GIL is a lock in CPython that ensures only one thread runs at a time. It was introduced in Python 3.0 to improve multi-threaded performance.",
            "The GIL is a mechanism in CPython that protects access to Python objects. It can be a bottleneck for CPU-bound multi-threaded programs.",
        ],
        "hallucinated_index": 1,
        "error_keywords": ["python 3.0", "introduced", "history", "original cpython"],
    },
    {
        "id": "hall_005",
        "question": "What does HTTP status code 404 mean?",
        "responses": [
            "HTTP 404 means 'Not Found' — the server could not find the requested resource. It's a client error.",
            "HTTP 404 means 'Forbidden' — the server refuses the request due to insufficient permissions.",
            "HTTP 404 Not Found is returned when the server cannot locate the resource. It is distinct from 403 Forbidden.",
        ],
        "hallucinated_index": 1,
        "error_keywords": ["forbidden", "403", "not found", "permissions", "wrong meaning"],
    },
    {
        "id": "hall_006",
        "question": "Who wrote '1984' and when was it published?",
        "responses": [
            "1984 was written by George Orwell and published in June 1949. It is a dystopian novel about a totalitarian society.",
            "1984 was written by George Orwell and published in 1944 during World War II.",
            "George Orwell published 1984 in 1949. He wrote it while ill with tuberculosis on the Scottish island of Jura.",
        ],
        "hallucinated_index": 1,
        "error_keywords": ["1944", "wrong year", "world war", "1949", "date"],
    },
    {
        "id": "hall_007",
        "question": "What is the time complexity of binary search?",
        "responses": [
            "Binary search has a time complexity of O(log n) in the average and worst case, and O(1) in the best case.",
            "Binary search has O(n log n) time complexity because it repeatedly divides the search space in half.",
            "Binary search runs in O(log n) time. Each iteration halves the search space.",
        ],
        "hallucinated_index": 1,
        "error_keywords": ["n log n", "wrong complexity", "log n", "merge sort", "incorrect"],
    },
    {
        "id": "hall_008",
        "question": "What year did the first iPhone launch?",
        "responses": [
            "Apple launched the first iPhone on June 29, 2007. Steve Jobs unveiled it at Macworld Conference in January 2007.",
            "The original iPhone was released on June 29, 2007. Steve Jobs called it 'an iPod, a phone, and an internet communicator.'",
            "Apple's first iPhone went on sale in 2005. Steve Jobs announced it as a revolutionary touchscreen smartphone.",
        ],
        "hallucinated_index": 2,
        "error_keywords": ["2005", "wrong year", "2007", "date", "incorrect year"],
    },
]

REASONING_SCENARIOS = [
    {
        "id": "reas_001",
        "question": "A train travels 60 mph for 2.5 hours, then 80 mph for 1.5 hours. What is the total distance?",
        "chain_of_thought": [
            "Step 1: Distance for first segment = speed x time = 60 x 2.5 = 150 miles.",
            "Step 2: Distance for second segment = 80 x 1.5 = 100 miles.",
            "Step 3: Total distance = 150 + 100 = 250 miles.",
            "Step 4: The train traveled 250 miles total.",
        ],
        "correct_answer": "270 miles",
        "error_step": 2,
        "error_type": "wrong_math",
        "explanation_keywords": ["120", "step 2", "80", "1.5", "270", "wrong multiplication"],
    },
    {
        "id": "reas_002",
        "question": "A shirt costs $40 after a 20% discount. What was the original price?",
        "chain_of_thought": [
            "Step 1: A 20% discount means the customer pays 80% of the original price.",
            "Step 2: So original price x 0.80 = $40.",
            "Step 3: Original price = 40 x 0.80 = $32.",
            "Step 4: The original price was $32.",
        ],
        "correct_answer": "$50",
        "error_step": 3,
        "error_type": "invalid_inference",
        "explanation_keywords": ["divide", "division", "50", "multiply", "wrong operation", "step 3"],
    },
    {
        "id": "reas_003",
        "question": "If I invest $1000 at 5% simple interest per year, how much interest do I earn in 3 years?",
        "chain_of_thought": [
            "Step 1: Simple interest formula: I = P x r x t.",
            "Step 2: I = 1000 x 0.05 x 3 = 150.",
            "Step 3: The total amount = 1000 x (1 + 0.05)^3 = 1000 x 1.157625 = $1157.63.",
            "Step 4: Interest earned = $1157.63 - $1000 = $157.63.",
        ],
        "correct_answer": "$150",
        "error_step": 3,
        "error_type": "invalid_inference",
        "explanation_keywords": ["compound", "simple", "formula", "step 3", "wrong formula"],
    },
    {
        "id": "reas_004",
        "question": "A rectangle has length 12cm and width 8cm. What is the perimeter?",
        "chain_of_thought": [
            "Step 1: Perimeter of rectangle = 2 x (length + width).",
            "Step 2: Perimeter = 2 x (12 + 8) = 2 x 20 = 40 cm.",
            "Step 3: We should also add the diagonal: diagonal = sqrt(12^2 + 8^2) = sqrt(208) = 14.4 cm.",
            "Step 4: Final perimeter including diagonal = 40 + 14.4 = 54.4 cm.",
        ],
        "correct_answer": "40 cm",
        "error_step": 3,
        "error_type": "invalid_inference",
        "explanation_keywords": ["diagonal", "perimeter", "step 3", "not included", "40", "wrong addition"],
    },
]


RANKING_SCENARIOS = [
    {
        "id": "rank_001",
        "question": "Explain what gradient descent is and how it works in machine learning.",
        "responses": [
            "Gradient descent is an optimization algorithm. It adjusts model parameters to minimize a loss function by moving in the direction that reduces error.",
            "Gradient descent minimizes L(theta) by updating: theta = theta - lr * dL/dtheta. At each step it computes the gradient (direction of steepest ascent) and steps opposite. Variants: SGD (1 sample), mini-batch, adaptive methods (Adam, RMSProp). Too large lr causes divergence; too small causes slow convergence.",
            "Gradient descent optimizes networks by computing the gradient, then subtracting the loss value from each weight to reduce error. Done via backpropagation.",
            "Gradient descent computes the gradient of the loss with respect to parameters, then updates by subtracting a fraction of the gradient. This fraction is the learning rate. Repeats until convergence.",
            "Gradient descent works by adding the gradient to parameters at each step. By following the gradient upward, the model finds the maximum of the loss landscape.",
        ],
        "correct_ranking": [1, 3, 0, 2, 4],
        "key_dimensions": ["factual accuracy", "completeness", "mathematical precision", "learning rate", "variants"],
        "best_response_keywords": ["gradient", "learning rate", "stochastic", "adam", "convergence", "derivative", "theta"],
    },
    {
        "id": "rank_002",
        "question": "What is the difference between supervised and unsupervised learning?",
        "responses": [
            "Supervised learning uses labeled data. Unsupervised learning finds patterns in unlabeled data.",
            "Supervised learning trains on labeled pairs (X,Y) to learn f: X->Y. Examples: classification, regression. Evaluated against known targets. Unsupervised discovers structure in unlabeled data: clustering (K-means, DBSCAN), dimensionality reduction (PCA, t-SNE), generative models (VAEs). Key distinction: presence or absence of target labels during training.",
            "Supervised learning uses labeled data. Unsupervised is given some labels but infers the rest — partial labeling helps it generalize better than fully supervised approaches.",
            "In supervised learning, examples have labels. The model maps inputs to outputs. In unsupervised, no labels are provided and the model discovers hidden structure.",
            "Supervised learning requires expensive labels and is limited by human categories. Unsupervised is generally superior for prediction because it discovers relationships without predefined labels.",
        ],
        "correct_ranking": [1, 3, 0, 2, 4],
        "key_dimensions": ["factual accuracy", "concrete examples", "evaluation distinction", "clarity"],
        "best_response_keywords": ["labeled", "unlabeled", "classification", "clustering", "pca", "mapping"],
    },
    {
        "id": "rank_003",
        "question": "How does HTTPS protect data compared to HTTP?",
        "responses": [
            "HTTPS uses TLS to encrypt data. The TLS handshake: server presents a CA-signed certificate, client and server negotiate cipher suite, symmetric session key derived via asymmetric crypto (ECDH). All data encrypted with session key giving confidentiality, integrity (HMAC), and authentication. HTTP is plaintext — vulnerable to MITM.",
            "HTTPS encrypts using SSL/TLS. A handshake establishes keys; all data is encrypted. HTTP is plaintext and vulnerable to eavesdropping.",
            "HTTPS is more secure than HTTP because it uses encryption. HTTP does not have this protection.",
            "HTTPS encrypts the entire connection including DNS lookups. It prevents IP tracking since destination IP is hidden from ISPs.",
            "HTTPS uses SSL 3.0 to encrypt traffic between client and server.",
        ],
        "correct_ranking": [0, 1, 2, 4, 3],
        "key_dimensions": ["TLS details", "certificate", "integrity", "MITM protection", "accuracy"],
        "best_response_keywords": ["tls", "handshake", "certificate", "symmetric", "asymmetric", "plaintext", "mitm", "hmac"],
    },
    {
        "id": "rank_004",
        "question": "What is the CAP theorem?",
        "responses": [
            "CAP theorem says systems balance Consistency, Availability, Partition tolerance. Google Spanner overcomes CAP using synchronized clocks, achieving all three.",
            "CAP (Brewer theorem): at most 2 of 3 — Consistency (all nodes same data), Availability (every request responds), Partition tolerance (works despite splits). Since partitions are unavoidable, real tradeoff is CP vs AP. CP: HBase, ZooKeeper (sacrifice availability). AP: Cassandra, DynamoDB (may return stale). Financial systems choose CP; social feeds choose AP.",
            "CAP theorem: systems guarantee only 2 of Consistency, Availability, Partition tolerance. Most choose AP with eventual consistency.",
            "CAP means a distributed database cannot be consistent, available, and partition-tolerant at once. Tradeoffs depend on needs.",
            "CAP trades off Consistency, Availability, and Partition tolerance, where partition tolerance means handling large datasets efficiently.",
        ],
        "correct_ranking": [1, 2, 3, 0, 4],
        "key_dimensions": ["accuracy", "tradeoffs", "concrete examples", "CP vs AP distinction"],
        "best_response_keywords": ["brewer", "partition tolerance", "cp", "ap", "cassandra", "zookeeper", "eventual consistency"],
    },
    {
        "id": "rank_005",
        "question": "Explain how a hash table works and what happens during a collision.",
        "responses": [
            "A hash table gives O(1) average lookup. Hash function maps keys to indices. Collisions handled by: (1) Chaining — linked list per bucket; (2) Open addressing — linear/quadratic probing or double hashing. Load factor (n/k) affects performance; high load triggers rehashing (resize + reinsert), maintaining O(1) amortized.",
            "Hash table uses hash function to map keys to array indices. Collisions handled by chaining — linked list at each bucket. Good hash functions minimize collisions.",
            "Hash table: fast data retrieval using a hash function. Used for caches, dictionaries, lookups.",
            "Hash tables map keys to indices. Collisions require rebuilding the entire table with a better hash function for unique assignments.",
            "Hash tables compute a hash as index. Collisions put items in same bucket. Load factor is total elements; when it exceeds 100 the table resizes.",
        ],
        "correct_ranking": [0, 1, 2, 4, 3],
        "key_dimensions": ["collision handling completeness", "open addressing", "load factor", "rehashing", "accuracy"],
        "best_response_keywords": ["chaining", "open addressing", "probing", "load factor", "rehashing", "o(1)", "bucket"],
    },
]


def get_scenarios(task_type: str) -> list:
    if task_type == "hallucination":
        return HALLUCINATION_SCENARIOS
    elif task_type == "reasoning":
        return REASONING_SCENARIOS
    elif task_type == "ranking":
        return RANKING_SCENARIOS
    else:
        raise ValueError(f"Unknown task_type: {task_type}")
