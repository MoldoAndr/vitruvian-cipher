OUT := thesis
SRC := main.tex
LATEXMK ?= latexmk
PLANTUML ?= plantuml
TEX_SOURCES := $(SRC) bibliography.bib
UML_SOURCES := $(wildcard images/*.uml)
UML_PDFS := $(UML_SOURCES:.uml=.pdf)

.PHONY: all pdf clean watch uml

all: uml pdf

uml: $(UML_PDFS)

images/%.pdf: images/%.uml
	@command -v $(PLANTUML) >/dev/null 2>&1 || { \
		echo "Eroare: utilitarul 'plantuml' nu este instalat."; \
		exit 1; \
	}
	$(PLANTUML) -tsvg $<
	inkscape $(<:.uml=.svg) --export-filename=$@
	rm -f $(<:.uml=.svg)

pdf: $(OUT).pdf

$(OUT).pdf: $(TEX_SOURCES) $(UML_PDFS)
	@command -v $(LATEXMK) >/dev/null 2>&1 || { \
		echo "Eroare: utilitarul 'latexmk' nu este instalat. Instalează-l (ex. 'sudo apt install latexmk') și reia comanda."; \
		exit 1; \
	}
	$(LATEXMK) -pdf -shell-escape -interaction=nonstopmode -jobname=$(OUT) $(SRC)

watch:
	@command -v $(LATEXMK) >/dev/null 2>&1 || { \
		echo "Eroare: utilitarul 'latexmk' nu este instalat."; \
		exit 1; \
	}
	$(LATEXMK) -pdf -pvc -interaction=nonstopmode -jobname=$(OUT) $(SRC)

clean:
	@command -v $(LATEXMK) >/dev/null 2>&1 && $(LATEXMK) -c -jobname=$(OUT) $(SRC) || true
	@rm -f $(OUT).bbl $(OUT).blg $(OUT).run.xml $(OUT)-blx.bib $(OUT).synctex.gz
