// C++ module demonstrating the public-symbol regex rows.
#include <stdexcept>
#include <string>

class Catalog {
public:
    std::string name;
};

struct CatalogConfig {
    int max_items;
};

int load_catalog(const std::string& path) {
    if (path.empty()) {
        throw CatalogError("path required");
    }
    return 0;
}

int save_catalog(const std::string& path) {
    if (path.empty()) {
        throw InvalidPathError("path required");
    }
    return 0;
}
