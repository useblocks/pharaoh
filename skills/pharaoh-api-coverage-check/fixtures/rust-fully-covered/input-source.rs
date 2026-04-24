//! Simple rust module demonstrating the rust classifier path.

pub struct Catalog {
    pub name: String,
}

pub enum CatalogError {
    NotFound,
    Unreadable,
}

pub trait Readable {
    fn read(&self) -> String;
}

impl Catalog {
    pub fn new(name: &str) -> Self {
        Catalog { name: name.to_string() }
    }

    pub fn rename(&mut self, name: &str) {
        self.name = name.to_string();
    }
}

pub fn load_catalog(path: &str) -> Catalog {
    Catalog::new(path)
}

pub fn save_catalog(cat: &Catalog, path: &str) -> bool {
    let _ = (cat, path);
    true
}

fn internal_helper() -> i32 {
    42
}
