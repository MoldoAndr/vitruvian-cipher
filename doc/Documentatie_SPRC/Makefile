OUT := thesis
SRC := main.tex
LATEXMK ?= latexmk
TEX_SOURCES := $(SRC) bibliography.bib

.PHONY: all pdf clean watch

all: pdf

pdf: $(OUT).pdf

$(OUT).pdf: $(TEX_SOURCES)
	@command -v $(LATEXMK) >/dev/null 2>&1 || { \
		echo "Eroare: utilitarul 'latexmk' nu este instalat. Instalează-l (ex. 'sudo apt install latexmk') și reia comanda."; \
		exit 1; \
	}
	$(LATEXMK) -pdf -interaction=nonstopmode -jobname=$(OUT) $(SRC)

watch:
	@command -v $(LATEXMK) >/dev/null 2>&1 || { \
		echo "Eroare: utilitarul 'latexmk' nu este instalat."; \
		exit 1; \
	}
	$(LATEXMK) -pdf -pvc -interaction=nonstopmode -jobname=$(OUT) $(SRC)

clean:
	@command -v $(LATEXMK) >/dev/null 2>&1 && $(LATEXMK) -c -jobname=$(OUT) $(SRC) || true
	@rm -f $(OUT).bbl $(OUT).blg $(OUT).run.xml $(OUT)-blx.bib $(OUT).synctex.gz
