#include <bits/stdc++.h>
using namespace std;

using Point = tuple<int64_t, int64_t>; 

constexpr int MAX_ITERATIONS = 100;

// Similarity function
double euclidean_distance(const Point& a, const Point& b) {
    int64_t dx = get<0>(a) - get<0>(b);
    int64_t dy = get<1>(a) - get<1>(b);
    return sqrt(dx * dx + dy * dy);
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    
    int n, k;
    cin >> n >> k;

    vector<Point> points(n);
    for (auto& [x, y] : points) {
        cin >> x >> y;
    }

    vector<Point> centroids(k);
    for (int i = 0; i < k; i++) {
        int centroid_index;
        cin >> centroid_index;
        centroids[i] = points[centroid_index - 1];
    }
    
    vector<int> assignments(n, -1);
    vector<Point> new_centroids(k);
    vector<int> counts(k);
    for (int iter = 0; iter < MAX_ITERATIONS; iter++) {
        // Assignment step
        for (int i = 0; i < n; i++) {
            double min_distance = numeric_limits<double>::max();
            int best_centroid = -1;
            for (int j = 0; j < k; j++) {
                double distance = euclidean_distance(points[i], centroids[j]);
                if (distance < min_distance) {
                    min_distance = distance;
                    best_centroid = j;
                }
            }
            assignments[i] = best_centroid;
        }

        // Update step
        for (auto &c : new_centroids) get<0>(c) = get<1>(c) = 0;
        fill(counts.begin(), counts.end(), 0);
        for (int i = 0; i < n; i++) {
            int cluster = assignments[i];
            get<0>(new_centroids[cluster]) += get<0>(points[i]);
            get<1>(new_centroids[cluster]) += get<1>(points[i]);
            counts[cluster]++;
        }
        for (int j = 0; j < k; j++) {
            if (counts[j] > 0) {
                get<0>(new_centroids[j]) /= counts[j];
                get<1>(new_centroids[j]) /= counts[j];
            } else {
                new_centroids[j] = centroids[j]; // Keep old centroid if no points assigned
            }
        }
        centroids = new_centroids;
    }

    for (const auto& assignment : assignments) {
        cout << assignment + 1 << "\n";
    }

    return 0;
}
