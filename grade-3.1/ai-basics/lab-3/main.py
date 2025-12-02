import numpy as np
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)

NUM_PARTICLES = 120
RESAMPLE_THRESHOLD = 0.5

rng = np.random.default_rng(seed=42)


class Polygon:
    def __init__(self, vertices):
        self.vertices = vertices
        
        self.edge_p1 = vertices
        self.edge_p2 = np.roll(vertices, -1, axis=0)
        self.edge_dx = self.edge_p2[:, 0] - self.edge_p1[:, 0]
        self.edge_dy = self.edge_p2[:, 1] - self.edge_p1[:, 1]
        
        self.min_x = vertices[:, 0].min()
        self.max_x = vertices[:, 0].max()
        self.min_y = vertices[:, 1].min()
        self.max_y = vertices[:, 1].max()

    def contains_point(self, point):
        if point.ndim == 1:
            point = point.reshape(1, -1)
        
        in_bbox = ((point[:, 0] >= self.min_x) & (point[:, 0] <= self.max_x) &
                   (point[:, 1] >= self.min_y) & (point[:, 1] <= self.max_y))
        
        n = len(self.vertices)
        inside = np.zeros(len(point), dtype=bool)
        
        for i in range(n):
            j = (i - 1) % n
            pi = self.vertices[i]
            pj = self.vertices[j]
            
            cond1 = (pi[1] > point[:, 1]) != (pj[1] > point[:, 1])
            cond2 = point[:, 0] < ((pj[0] - pi[0]) * (point[:, 1] - pi[1]) / 
                                   (pj[1] - pi[1]) + pi[0])
            
            inside ^= (cond1 & cond2)
        
        return inside & in_bbox

    def random_point_inside(self, n=1):
        points = []
        while len(points) < n:
            x = rng.uniform(self.min_x, self.max_x, n - len(points))
            y = rng.uniform(self.min_y, self.max_y, n - len(points))
            candidates = np.column_stack([x, y])
            valid = self.contains_point(candidates)
            points.extend(candidates[valid])
        
        return np.array(points[:n])


def raycast_vectorized(polygon, points, angles):
    N = points.shape[0]
    K = len(angles)
    
    dx = np.cos(angles)
    dy = np.sin(angles)
    
    min_dist = np.full((N, K), np.inf)
    
    for i in range(len(polygon.edge_p1)):
        edge_p1 = polygon.edge_p1[i]
        edge_dx = polygon.edge_dx[i]
        edge_dy = polygon.edge_dy[i]
        
        denom = dx[np.newaxis, :] * edge_dy - dy[np.newaxis, :] * edge_dx
        
        valid = np.abs(denom) >= 1e-12
        
        diff_x = edge_p1[0] - points[:, 0:1]
        diff_y = edge_p1[1] - points[:, 1:2]
        
        t = (diff_x * edge_dy - diff_y * edge_dx) / (denom + 1e-300)
        s = (diff_x * dy[np.newaxis, :] - diff_y * dx[np.newaxis, :]) / (denom + 1e-300)
        
        valid_intersection = valid & (t > 1e-9) & (s >= 0.0) & (s <= 1.0)
        min_dist = np.where(valid_intersection, np.minimum(min_dist, t), min_dist)
    
    return min_dist


def measurement_log_vectorized(polygon, particles, measurements, sl):
    inside = polygon.contains_point(particles)
    
    k = len(measurements)
    angles = np.linspace(0, 2 * np.pi, k, endpoint=False)
    
    expected = raycast_vectorized(polygon, particles, angles)
    
    inv_2var = 0.5 / (sl ** 2)
    valid = expected < (np.inf / 2.0)
    
    diff_sq = (measurements[np.newaxis, :] - expected) ** 2
    log_likelihood = -np.sum(diff_sq * valid * inv_2var, axis=1)
    
    log_likelihood[~inside] = -np.inf
    return log_likelihood


def resample(weights, particles):
    weight_sum_sq = np.sum(weights ** 2)
    effective_sample_size = 1.0 / weight_sum_sq if weight_sum_sq > 1e-300 else 0.0
    
    if effective_sample_size >= RESAMPLE_THRESHOLD * len(weights):
        return None
    
    cumsum = np.cumsum(weights)
    positions = (np.arange(NUM_PARTICLES) + rng.uniform(0, 1)) / NUM_PARTICLES
    
    indices = np.searchsorted(cumsum, positions)
    indices = np.clip(indices, 0, len(particles) - 1)
    
    return particles[indices].copy()


def calculate_weights(polygon, particles, measurements, sl):
    log_weights = measurement_log_vectorized(polygon, particles, measurements, sl)
    
    max_log_weight = np.max(log_weights)
    weights = np.exp(log_weights - max_log_weight)
    
    weight_sum = np.sum(weights)
    
    if weight_sum > 1e-300:
        weights /= weight_sum
    else:
        weights = np.ones(len(particles)) / len(particles)
    
    return weights


def particle_filter(polygon, movements, start_position, sl, sx, sy):
    if start_position is not None:
        particles = rng.normal(0, [sx, sy], size=(NUM_PARTICLES, 2)) + start_position
    else:
        particles = polygon.random_point_inside(NUM_PARTICLES)

    weights = np.ones(NUM_PARTICLES) / NUM_PARTICLES
    
    for lidar, movement in movements:
        weights = calculate_weights(polygon, particles, lidar, sl)
        
        resampled = resample(weights, particles)
        if resampled is not None:
            particles = resampled
        
        if movement is not None:
            noise = rng.normal(0, [sx, sy], size=(NUM_PARTICLES, 2))
            particles += movement + noise
    
    final_position = np.sum(particles * weights[:, np.newaxis], axis=0)
    
    return final_position


def main():
    _particles_count = int(input())
    polygon_data = np.array(list(map(float, input().split())))
    vertices = polygon_data.reshape(-1, 2)
    polygon = Polygon(vertices)
    
    movements_count, _ = map(int, input().split())
    sl, sx, sy = map(float, input().split())
    
    start_data = list(map(float, input().split()))
    if int(start_data[0]) != 0:
        start_position = np.array([start_data[1], start_data[2]])
    else:
        start_position = None
    
    movements = []
    for _ in range(movements_count):
        lidar = np.array(list(map(float, input().split())))
        movement = np.array(list(map(float, input().split())))
        movements.append((lidar, movement))
    
    last_data = np.array(list(map(float, input().split())))
    movements.append((last_data, None))
    
    final_position = particle_filter(polygon, movements, start_position, sl, sx, sy)
    print(final_position[0], final_position[1])


if __name__ == "__main__":
    main()
