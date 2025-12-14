use serde_json::Value;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Test {
    pub right: u64,
    pub acute: u64,
    pub obtuse: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TestWithPath {
    pub right: u64,
    pub acute: u64,
    pub obtuse: u64,
    pub path: String
}

impl TestWithPath {
    pub fn from_json(value: &Value) -> Option<Self> {
        Some(Self {
            right: value.get("right")?.as_u64()?,
            acute: value.get("acute")?.as_u64()?,
            obtuse: value.get("obtuse")?.as_u64()?,
            path: value.get("path")?.as_str()?.to_string(),
        })
    }

    pub fn array_from_json(value: &Value) -> Option<Vec<Self>> {
        value.as_array()?.iter().map(Self::from_json).collect()
    }

    pub fn array_from_json_file(path: &str) -> Option<Vec<Self>> {
        let stream = std::fs::File::open(path).ok()?;
        let json: Value = serde_json::from_reader(stream).ok()?;
        Self::array_from_json(&json)
    }
}

impl From<&TestWithPath> for Test {
    fn from(test_with_path: &TestWithPath) -> Self {
        Self {
            right: test_with_path.right,
            acute: test_with_path.acute,
            obtuse: test_with_path.obtuse,
        }
    }
}
