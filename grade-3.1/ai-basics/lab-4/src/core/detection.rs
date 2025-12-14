use std::path;

use crate::schema::{
    test::Test,
    triangle::{Triangle, TriangleType},
};
use opencv::{
    core::{
        AlgorithmHint, BORDER_DEFAULT, Mat, MatTraitConst, Point, Scalar, Size, Vector
    },
    imgcodecs::imwrite,
    imgproc,
    prelude::VectorToVec,
};

/// Compute aspect ratio (height/width) of a triangle's bounding box
fn aspect_ratio(t: &Triangle) -> f64 {
    let xs: Vec<i32> = t.vertices.iter().map(|p| p.x).collect();
    let ys: Vec<i32> = t.vertices.iter().map(|p| p.y).collect();
    let width = (xs.iter().max().unwrap() - xs.iter().min().unwrap()) as f64;
    let height = (ys.iter().max().unwrap() - ys.iter().min().unwrap()) as f64;
    if width < 1.0 { height } else { height / width }
}

/// Check if two triangles are duplicates based on centroid proximity and perimeter similarity
fn is_duplicate(
    t1: &Triangle,
    t2: &Triangle,
    centroid_thresh: f64,
    perimeter_ratio_thresh: f64,
) -> bool {
    // Centroid distance check
    let xpow = (t1.centroid.x - t2.centroid.x).pow(2) as f64;
    let ypow = (t1.centroid.y - t2.centroid.y).pow(2) as f64;
    let dist = (xpow + ypow).sqrt();

    // Perimeter similarity - better than area for distinguishing:
    // Inner/outer duplicates: perimeter ratio ~0.92-0.98 (very similar)
    // Nested triangles: perimeter ratio ~0.5-0.85 (quite different)
    let min_p = t1.perimeter.min(t2.perimeter);
    let max_p = t1.perimeter.max(t2.perimeter);
    let perimeter_ratio = min_p / max_p;

    // Compare aspect ratios - tall vs wide triangles should not be duplicates
    let ar1 = aspect_ratio(t1);
    let ar2 = aspect_ratio(t2);
    let ar_min = ar1.min(ar2);
    let ar_max = ar1.max(ar2);
    let ar_ratio = if ar_max < 0.01 { 1.0 } else { ar_min / ar_max };

    // Duplicates: close centroids, very similar perimeter, similar aspect ratio
    dist < centroid_thresh
        && perimeter_ratio > perimeter_ratio_thresh
        && ar_ratio > 0.5
}

/// Process contours from a preprocessed image and extract triangles
fn process_contours(
    contours: &Vector<Vector<Point>>,
    min_area: f64,
    max_area: f64,
    min_perimeter: f64,
    epsilon_factor: f64,
    centroid_threshold: f64,
    perimeter_ratio_threshold: f64,
) -> Vec<Triangle> {
    let mut found_triangles: Vec<Triangle> = Vec::new();
    for contour in contours.iter() {
        // Calculate contour area
        let area = imgproc::contour_area(&contour, false).unwrap_or(0.0);
        if area < min_area || area > max_area {
            continue;
        }

        // Check perimeter to filter small noise
        let perimeter = imgproc::arc_length(&contour, true).unwrap_or(0.0);
        if perimeter < min_perimeter {
            continue;
        }

        // Approximate the contour to a polygon
        let mut approx: Vector<Point> = Vector::new();
        let epsilon = epsilon_factor * perimeter;
        if imgproc::approx_poly_dp(&contour, &mut approx, epsilon, true)
            .is_err()
        {
            continue;
        }

        // Check if it's a triangle (3 vertices)
        if approx.len() != 3 {
            continue;
        }

        // Get vertices
        let vertices_vec: Vec<Point> = approx.to_vec();
        let vertices = [vertices_vec[0], vertices_vec[1], vertices_vec[2]];

        // Classify the triangle
        let triangle = Triangle::new(vertices);

        // Check if duplicate
        let dup = found_triangles.iter().any(|existing| {
            is_duplicate(
                existing,
                &triangle,
                centroid_threshold,
                perimeter_ratio_threshold,
            )
        });

        if !dup {
            found_triangles.push(triangle);
        }
    }
    found_triangles
}

fn save_debug_image(
    found_triangles: &Vec<Triangle>,
    img: &Mat,
    angle_tolerance: f64,
) -> Result<(), opencv::Error> {
    let folder = path::absolute("assets/exports").unwrap();
    std::fs::create_dir_all(&folder).ok();

    let path = path::absolute(format!(
        "{}/{}.png",
        folder.display(),
        chrono::Local::now().format("%Y%m%d_%H%M%S%.3f")
    ))
    .unwrap();
    let path = path.to_str().unwrap();

    // Put red dots on detected triangle vertices
    let mut debug_img = img.clone();
    for triangle in found_triangles {
        for &vertex in &triangle.vertices {
            imgproc::circle(
                &mut debug_img,
                vertex,
                5,
                Scalar::new(0.0, 0.0, 255.0, 0.0),
                -1,
                imgproc::LINE_8,
                0,
            )
            .ok();
        }

        // On centroid, put type text
        let triangle_type = match triangle.classify(angle_tolerance) {
            TriangleType::Right => "Right",
            TriangleType::Acute => "Acute",
            TriangleType::Obtuse => "Obtuse",
        };
        imgproc::put_text(
            &mut debug_img,
            triangle_type,
            triangle.centroid,
            imgproc::FONT_HERSHEY_SIMPLEX,
            0.5,
            Scalar::new(255.0, 0.0, 0.0, 0.0),
            1,
            imgproc::LINE_8,
            false,
        )
        .ok();
    }

    imwrite(&path, &debug_img, &Vector::new())?;
    Ok(())
}

pub fn triangles_stats(
    img: &Mat,
    angle_tolerance: f64,
) -> Result<Test, opencv::Error> {
    let image_area = (img.rows() * img.cols()) as f64;
    let image_dim = image_area.sqrt();
    let min_area = image_area * 0.001;
    let max_area = image_area * 0.5;
    let min_perimeter = image_dim * 0.05;

    // Threshold for centroid distance to consider triangles as duplicates
    let centroid_threshold = image_dim * 0.025;

    // Perimeter ratio threshold - inner/outer duplicates have ratio ~0.75-0.98
    // Nested triangles have much lower ratio (~0.4-0.7), so we use 0.75 as threshold
    let perimeter_ratio_threshold = 0.75;

    // Convert to grayscale
    let mut gray = Mat::default();
    imgproc::cvt_color(
        img,
        &mut gray,
        imgproc::COLOR_BGR2GRAY,
        0,
        AlgorithmHint::ALGO_HINT_DEFAULT,
    )?;

    // Strong bilateral filter to blur grid while preserving strong edges
    let mut filtered = Mat::default();
    imgproc::bilateral_filter(
        &gray,
        &mut filtered,
        9,
        75.0,
        75.0,
        BORDER_DEFAULT,
    )?;

    let mut edges = Mat::default();
    imgproc::canny(&filtered, &mut edges, 50.0, 150.0, 3, false)?;

    // Morphological closing to bridge small gaps in contours (before dilation)
    let close_kernel = imgproc::get_structuring_element(
        imgproc::MORPH_ELLIPSE,
        Size::new(5, 5),
        Point::new(-1, -1),
    )?;
    let mut closed = Mat::default();
    imgproc::morphology_ex(
        &edges,
        &mut closed,
        imgproc::MORPH_CLOSE,
        &close_kernel,
        Point::new(-1, -1),
        1,
        BORDER_DEFAULT,
        Scalar::default(),
    )?;

    let dilate_kernel = imgproc::get_structuring_element(
        imgproc::MORPH_RECT,
        Size::new(3, 3),
        Point::new(-1, -1),
    )?;

    // Standard dilation (2 iterations)
    let mut dilated = Mat::default();
    imgproc::dilate(
        &closed,
        &mut dilated,
        &dilate_kernel,
        Point::new(-1, -1),
        2,
        BORDER_DEFAULT,
        Scalar::default(),
    )?;

    let mut contours: Vector<Vector<Point>> = Vector::new();
    imgproc::find_contours(
        &dilated,
        &mut contours,
        imgproc::RETR_LIST,
        imgproc::CHAIN_APPROX_SIMPLE,
        Point::new(0, 0),
    )?;

    let found_triangles = process_contours(
        &contours,
        min_area,
        max_area,
        min_perimeter,
        0.03,
        centroid_threshold,
        perimeter_ratio_threshold,
    );

    save_debug_image(&found_triangles, &img, angle_tolerance)?;
    save_debug_image(&found_triangles, &dilated, angle_tolerance)?;

    // Count triangle types
    let (mut right, mut acute, mut obtuse) = (0, 0, 0);

    for triangle in &found_triangles {
        match triangle.classify(angle_tolerance) {
            TriangleType::Right => right += 1,
            TriangleType::Acute => acute += 1,
            TriangleType::Obtuse => obtuse += 1,
        }
    }

    Ok(Test { right, acute, obtuse })
}
