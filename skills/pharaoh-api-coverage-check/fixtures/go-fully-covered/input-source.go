// Package inventory demonstrates the go public-symbol regex row.
package inventory

type Catalog struct {
	Name string
}

type Reader interface {
	Read() string
}

func LoadCatalog(path string) *Catalog {
	return &Catalog{Name: path}
}

func SaveCatalog(cat *Catalog, path string) bool {
	_ = cat
	_ = path
	return true
}

func internalHelper() int {
	return 42
}

type privateState struct {
	token string
}
