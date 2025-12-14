use opencv::core::Point;

const ORDERS: [(usize, usize, usize); 3] = [(1, 0, 2), (0, 1, 2), (0, 2, 1)];

#[derive(Debug)]
pub enum TriangleType {
    Right,
    Acute,
    Obtuse,
}

fn distance(p1: Point, p2: Point) -> f64 {
    let dx = (p1.x - p2.x) as f64;
    let dy = (p1.y - p2.y) as f64;
    (dx * dx + dy * dy).sqrt()
}

#[derive(Clone, Copy, Debug)]
pub struct Triangle {
    pub vertices: [Point; 3],
    pub angles: [f64; 3],
    pub area: f64,
    pub perimeter: f64,
    pub centroid: Point,
}

impl Triangle {
    fn area_and_perimeter(vertices: &[Point; 3]) -> (f64, f64) {
        let a = distance(vertices[0], vertices[1]);
        let b = distance(vertices[1], vertices[2]);
        let c = distance(vertices[2], vertices[0]);
        let perimeter = a + b + c;
        let s = perimeter / 2.0;
        let area = (s * (s - a) * (s - b) * (s - c)).sqrt();
        (area, perimeter)
    }

    fn centroid(vertices: &[Point; 3]) -> Point {
        Point {
            x: (vertices[0].x + vertices[1].x + vertices[2].x) / 3,
            y: (vertices[0].y + vertices[1].y + vertices[2].y) / 3,
        }
    }

    pub fn new(vertices: [Point; 3]) -> Self {
        let (area, perimeter) = Self::area_and_perimeter(&vertices);
        let centroid = Self::centroid(&vertices);
        let angles = Self::angles(&vertices);
        Self { vertices, area, perimeter, centroid, angles }
    }

    fn angles(vertices: &[Point; 3]) -> [f64; 3] {
        let mut angles = ORDERS.map(|(a, b, c)| {
            let (p1, vertex, p2) =
                (vertices[a], vertices[b], vertices[c]);

            let v1 = ((p1.x - vertex.x) as f64, (p1.y - vertex.y) as f64);
            let v2 = ((p2.x - vertex.x) as f64, (p2.y - vertex.y) as f64);

            let dot = v1.0 * v2.0 + v1.1 * v2.1;
            let mag1 = (v1.0 * v1.0 + v1.1 * v1.1).sqrt();
            let mag2 = (v2.0 * v2.0 + v2.1 * v2.1).sqrt();

            if mag1 < 1e-6 || mag2 < 1e-6 {
                return 0.0;
            }

            let cos_angle = (dot / (mag1 * mag2)).clamp(-1.0, 1.0);
            cos_angle.acos().to_degrees()
        });
        angles.sort_by(f64::total_cmp);
        angles
    }

    pub fn classify(&self, angle_tolerance: f64) -> TriangleType {
        let angles = self.angles;
        let max_angle = angles[2];

        if (max_angle - 90.0).abs() <= angle_tolerance {
            TriangleType::Right
        } else if max_angle < 90.0 {
            TriangleType::Acute
        } else {
            TriangleType::Obtuse
        }
    }
}
