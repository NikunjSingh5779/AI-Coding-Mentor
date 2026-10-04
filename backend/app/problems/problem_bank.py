"""
Sample Problem Bank for AI Real-Time Coding Screener
"""

PROBLEMS = [
    {
        "id": "fibonacci_basic",
        "title": "Fibonacci Sequence",
        "description": """Write a function that returns the nth number in the Fibonacci sequence.

The Fibonacci sequence starts with 0, 1, and each subsequent number is the sum of the two preceding ones.
F(0) = 0, F(1) = 1, F(n) = F(n-1) + F(n-2)

Examples:
- fibonacci(0) should return 0
- fibonacci(1) should return 1
- fibonacci(5) should return 5
- fibonacci(10) should return 55""",
        "difficulty": "beginner",
        "category": "algorithms",
        "starter_code": """def fibonacci(n):
    # TODO: Implement fibonacci sequence
    # Hint: Consider using iteration or recursion
    pass

# Test your function
print(fibonacci(0))  # Should print 0
print(fibonacci(1))  # Should print 1
print(fibonacci(5))  # Should print 5
print(fibonacci(10)) # Should print 55""",
        "solution": """def fibonacci(n):
    if n <= 1:
        return n

    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b""",
        "test_cases": [
            {"input": {"n": 0}, "expected": 0, "description": "Base case: F(0)"},
            {"input": {"n": 1}, "expected": 1, "description": "Base case: F(1)"},
            {"input": {"n": 2}, "expected": 1, "description": "F(2) = F(1) + F(0)"},
            {"input": {"n": 5}, "expected": 5, "description": "F(5)"},
            {"input": {"n": 10}, "expected": 55, "description": "F(10)"},
        ],
    },
    {
        "id": "palindrome_check",
        "title": "Palindrome Checker",
        "description": """Write a function that checks if a string is a palindrome.

A palindrome reads the same forwards and backwards (ignoring case and spaces).

Examples:
- is_palindrome("racecar") should return True
- is_palindrome("A man a plan a canal Panama") should return True
- is_palindrome("hello") should return False""",
        "difficulty": "beginner",
        "category": "strings",
        "starter_code": """def is_palindrome(s):
    # TODO: Check if string is a palindrome
    # Hint: Consider normalizing the string first
    pass

# Test your function
print(is_palindrome("racecar"))  # Should print True
print(is_palindrome("A man a plan a canal Panama"))  # Should print True
print(is_palindrome("hello"))  # Should print False""",
        "solution": """def is_palindrome(s):
    # Normalize: convert to lowercase and remove spaces
    normalized = ''.join(s.lower().split())
    # Check if it reads the same forwards and backwards
    return normalized == normalized[::-1]""",
        "test_cases": [
            {
                "input": {"s": "racecar"},
                "expected": True,
                "description": "Simple palindrome",
            },
            {
                "input": {"s": "A man a plan a canal Panama"},
                "expected": True,
                "description": "Palindrome with spaces",
            },
            {
                "input": {"s": "hello"},
                "expected": False,
                "description": "Not a palindrome",
            },
            {
                "input": {"s": "Madam"},
                "expected": True,
                "description": "Case insensitive",
            },
            {"input": {"s": ""}, "expected": True, "description": "Empty string"},
        ],
    },
    {
        "id": "sum_of_digits",
        "title": "Sum of Digits",
        "description": """Write a function that calculates the sum of all digits in a positive integer.

Examples:
- sum_of_digits(123) should return 6 (1 + 2 + 3)
- sum_of_digits(999) should return 27 (9 + 9 + 9)
- sum_of_digits(5) should return 5""",
        "difficulty": "beginner",
        "category": "mathematics",
        "starter_code": """def sum_of_digits(n):
    # TODO: Calculate sum of all digits in n
    # Hint: You can convert to string or use modulo arithmetic
    pass

# Test your function
print(sum_of_digits(123))  # Should print 6
print(sum_of_digits(999))  # Should print 27
print(sum_of_digits(5))    # Should print 5""",
        "solution": """def sum_of_digits(n):
    total = 0
    while n > 0:
        total += n % 10
        n //= 10
    return total""",
        "test_cases": [
            {"input": {"n": 123}, "expected": 6, "description": "Multiple digits"},
            {"input": {"n": 999}, "expected": 27, "description": "Same digits"},
            {"input": {"n": 5}, "expected": 5, "description": "Single digit"},
            {"input": {"n": 1000}, "expected": 1, "description": "With zeros"},
        ],
    },
    {
        "id": "find_maximum",
        "title": "Find Maximum in List",
        "description": """Write a function that finds the maximum value in a list of numbers.

Do not use the built-in max() function.

Examples:
- find_max([1, 3, 2, 8, 5]) should return 8
- find_max([-1, -5, -2]) should return -1
- find_max([42]) should return 42""",
        "difficulty": "beginner",
        "category": "arrays",
        "starter_code": """def find_max(numbers):
    # TODO: Find the maximum value without using max()
    # Hint: Iterate through the list and keep track of the largest seen
    pass

# Test your function
print(find_max([1, 3, 2, 8, 5]))  # Should print 8
print(find_max([-1, -5, -2]))     # Should print -1
print(find_max([42]))              # Should print 42""",
        "solution": """def find_max(numbers):
    if not numbers:
        return None

    maximum = numbers[0]
    for num in numbers[1:]:
        if num > maximum:
            maximum = num
    return maximum""",
        "test_cases": [
            {
                "input": {"numbers": [1, 3, 2, 8, 5]},
                "expected": 8,
                "description": "Mixed positive numbers",
            },
            {
                "input": {"numbers": [-1, -5, -2]},
                "expected": -1,
                "description": "All negative numbers",
            },
            {
                "input": {"numbers": [42]},
                "expected": 42,
                "description": "Single element",
            },
            {
                "input": {"numbers": [5, 5, 5]},
                "expected": 5,
                "description": "All same numbers",
            },
        ],
    },
    {
        "id": "count_vowels",
        "title": "Count Vowels",
        "description": """Write a function that counts the number of vowels (a, e, i, o, u) in a string.

The function should be case-insensitive.

Examples:
- count_vowels("hello") should return 2
- count_vowels("PROGRAMMING") should return 3
- count_vowels("xyz") should return 0""",
        "difficulty": "beginner",
        "category": "strings",
        "starter_code": """def count_vowels(text):
    # TODO: Count vowels (a, e, i, o, u) case-insensitively
    # Hint: Convert to lowercase and check each character
    pass

# Test your function
print(count_vowels("hello"))        # Should print 2
print(count_vowels("PROGRAMMING"))  # Should print 3
print(count_vowels("xyz"))          # Should print 0""",
        "solution": """def count_vowels(text):
    vowels = "aeiou"
    count = 0
    for char in text.lower():
        if char in vowels:
            count += 1
    return count""",
        "test_cases": [
            {"input": {"text": "hello"}, "expected": 2, "description": "Mixed case"},
            {
                "input": {"text": "PROGRAMMING"},
                "expected": 3,
                "description": "Uppercase",
            },
            {"input": {"text": "xyz"}, "expected": 0, "description": "No vowels"},
            {"input": {"text": "aeiou"}, "expected": 5, "description": "All vowels"},
            {"input": {"text": ""}, "expected": 0, "description": "Empty string"},
        ],
    },
]


def get_problem(problem_id: str):
    """Get a problem by ID"""
    for problem in PROBLEMS:
        if problem["id"] == problem_id:
            return problem
    return None


def get_problems_by_difficulty(difficulty: str):
    """Get problems filtered by difficulty"""
    return [p for p in PROBLEMS if p["difficulty"] == difficulty]


def get_problems_by_category(category: str):
    """Get problems filtered by category"""
    return [p for p in PROBLEMS if p["category"] == category]


def list_all_problems():
    """Get all available problems"""
    return PROBLEMS
