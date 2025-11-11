#include <bits/stdc++.h>
using namespace std;

vector<string> read_array(int count_lines, bool split = false) {
    vector<string> result;
    string line;
    for (int i = 0; i < count_lines; i++) {
        getline(cin >> ws, line);
        if (split) {
            istringstream iss(line);
            string word;
            while (iss >> word) result.push_back(word);
        } else {
            result.push_back(line);
        }
    }
    return result;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m, k;
    cin >> n >> m >> k;
    cin.ignore();

    vector<string> normal_emails = read_array(n, true);
    vector<string> spam_emails = read_array(m, true);

    double vocabulary_size = n + m;

    double prob_normal = n / vocabulary_size;
    double prob_spam   = m / vocabulary_size;

    unordered_map<string, double> probs_normal, probs_spam;

    // Compute word probabilities
    for (const auto& word : normal_emails)
        probs_normal[word]++;

    for (const auto& word : spam_emails)
        probs_spam[word]++;

    // Turn counts into probabilities
    for (auto& [word, count] : probs_normal)
        count /= normal_emails.size();

    for (auto& [word, count] : probs_spam)
        count /= spam_emails.size();

    vector<string> new_emails = read_array(k);
    for (const auto& new_email : new_emails) {
        istringstream iss(new_email);
        string w;
        double prob_spam_in_email = prob_spam;
        double prob_normal_in_email = prob_normal;

        while (iss >> w) {
            prob_spam_in_email   *= probs_spam.count(w)   ? probs_spam[w]   : 0.0;
            prob_normal_in_email *= probs_normal.count(w) ? probs_normal[w] : 0.0;
        }

        double denominator = prob_spam_in_email + prob_normal_in_email;
        double prob_email_is_spam = (denominator == 0) ? 0 : prob_spam_in_email / denominator;

        cout << prob_email_is_spam << "\n";
    }

    return 0;
}
