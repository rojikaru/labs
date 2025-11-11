#include <bits/stdc++.h>
using namespace std;

struct House {
    int64_t floors;
    int64_t rooms;

    // Distances in meters
    int64_t distance_to_downtown;
    int64_t distance_to_school;
    int64_t distance_to_mall;

    // Area in square meters
    int64_t area;

    optional<int64_t> price = nullopt;

    static House from_input(istream& in, bool include_price = true) {
        House house;
        in >> house.floors >> house.rooms
           >> house.distance_to_downtown >> house.distance_to_school >> house.distance_to_mall
           >> house.area;

        if (include_price) {
            int64_t price;
            in >> price;
            house.price = price;
        }

        return house;
    }
};

double similarity_metric(const House& a, const House& b) {
    // Euclidean distance in feature space
    double sum = 0.0;
    sum += pow(a.floors - b.floors, 2);
    sum += pow(a.rooms - b.rooms, 2);
    sum += pow(a.distance_to_downtown - b.distance_to_downtown, 2);
    sum += pow(a.distance_to_school - b.distance_to_school, 2);
    sum += pow(a.distance_to_mall - b.distance_to_mall, 2);
    sum += pow(a.area - b.area, 2);
    return sqrt(sum);
}

vector<tuple<House, double>> similarity_metric(const House& target, const vector<House>& candidates, optional<size_t> limit = nullopt) {
    vector<tuple<House, double>> similarities;
    similarities.reserve(candidates.size());

    for (const auto& candidate : candidates) {
        double sim = similarity_metric(target, candidate);
        similarities.emplace_back(candidate, sim);
    }

    // Sort by similarity (lower is more similar)
    sort(similarities.begin(), similarities.end(), [](const auto& a, const auto& b) {
        return get<1>(a) < get<1>(b);
    });

    if (limit.has_value() && similarities.size() > limit.value()) {
        similarities.resize(limit.value());
    }

    return similarities;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    
    uint32_t n, m, k;
    cin >> n >> m >> k;

    vector<House> houses_with_prices(n);
    for (auto& house : houses_with_prices) {
        house = House::from_input(cin);
    }

    vector<House> houses_without_prices(m);
    for (auto& house : houses_without_prices) {
        house = House::from_input(cin, false);
        auto top_k = similarity_metric(house, houses_with_prices, k);

        double avg = 0.0;
        for (const auto& [similar_house, _] : top_k) {
            avg += similar_house.price.value();
        }
        avg /= top_k.size();
        cout << avg << '\n';
    }

    return 0;
}
