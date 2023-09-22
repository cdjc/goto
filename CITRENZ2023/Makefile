
# Define the LaTeX source file and the PDF output file
TEX_SOURCE = CITRENZ2023.tex
PDF_OUTPUT = CITRENZ2023.pdf

# Define LaTeX compiler and options
LATEX_COMPILER = pdflatex
LATEX_OPTIONS = -interaction=nonstopmode -shell-escape

# Default target: build the PDF
all: $(PDF_OUTPUT)

# Rule to build the PDF from the LaTeX source
$(PDF_OUTPUT): $(TEX_SOURCE)
	$(LATEX_COMPILER) $(LATEX_OPTIONS) $(TEX_SOURCE)
	$(LATEX_COMPILER) $(LATEX_OPTIONS) $(TEX_SOURCE)

# Clean up intermediate files
clean:
	rm -f *.aux *.log *.out *.toc

# Clean up all generated files, including the PDF
distclean: clean
	rm -f $(PDF_OUTPUT)

# Open the PDF using the default viewer
view: $(PDF_OUTPUT)
	evince $(PDF_OUTPUT)

# Phony targets (targets that don't represent files)
.PHONY: all clean distclean view