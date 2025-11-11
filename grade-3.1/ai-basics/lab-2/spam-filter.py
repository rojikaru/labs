import numpy as np


def read_array(count_lines: int, split=False):
    if split:
        return np.array([word for _ in range(count_lines) for word in input().split()])
    else:
        return np.array([input() for _ in range(count_lines)])


def main():
    n, m, k = map(int, input().split())

    normal_emails = read_array(n, split=True)
    spam_emails = read_array(m, split=True)

    vocabulary_size = n + m

    prob_normal = n / vocabulary_size
    probs_normal = {
        word: np.sum(normal_emails == word) / len(normal_emails)
        for word in set(normal_emails)
    }

    prob_spam = m / vocabulary_size
    probs_spam = {
        word: np.sum(spam_emails == word) / len(spam_emails) 
        for word in set(spam_emails)
    }

    new_emails = read_array(k)
    for new_email in new_emails:
        new_email_words = np.array(new_email.split())

        # cumulative probability of having spam words
        prob_spam_in_email = (
            prob_spam
            * np.array([probs_spam.get(word, 0) for word in new_email_words]).prod()
        )

        # probability of not spam
        prob_normal_in_email = (
            prob_normal
            * np.array([probs_normal.get(word, 0) for word in new_email_words]).prod()
        )

        prob_email_is_spam = prob_spam_in_email / (
            prob_spam_in_email + prob_normal_in_email
        )
        print(prob_email_is_spam)


if __name__ == "__main__":
    main()
