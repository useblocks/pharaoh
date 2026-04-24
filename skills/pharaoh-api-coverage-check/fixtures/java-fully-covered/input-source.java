package com.example.inventory;

public class Catalog {
    public String name;
}

public interface Reader {
    String read();
}

public class CatalogService {
    public int loadCatalog(String path) {
        if (path == null) {
            throw new CatalogError("path required");
        }
        return 0;
    }

    public int saveCatalog(String path) {
        if (path == null) {
            throw new InvalidPathError("path required");
        }
        return 0;
    }
}

class InternalHelper {
    int compute(int x) { return x; }
}
