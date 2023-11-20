// Get Polylux from the official package repository
#import "@preview/polylux:0.3.1": *
// #import themes.simple: *
#import themes.clean: *
// Make the paper dimensions fit for a presentation and the text larger
#set page(paper: "presentation-16-9")
// #set text(size: 22pt)
#set text(font: "DejaVu Sans")

#show link: underline

// #show: simple-theme.with(
//   footer: [Simple slides],
// )

#show: clean-theme.with(
  footer: "Carl Cerecke"

)

//#set text(size: 22pt)
// Use #polylux-slide to create a slide and style it using your favourite Typst functions
#slide()[
  #align(horizon + center)[
    #v(2em)

    = Recreating goto in Python
    #v(1em)

    Carl Cerecke carl.cerecke\@nmit.ac.nz

    #v(2em)
    CITENZ 2023 Auckland

    September 27-29, 2023

    #v(2em)
    #link("http://github/cdjc/goto")[http://github/cdjc/goto]
  ]
]

#slide(title: "Outline")[
  + Memories
  + Motiviation
  + Mechanism
  + Measurement
  + Musings
]

#slide(title: "Memories: A short history of goto")[
  #set text(size: 22pt)

  - In the beginning was the goto
  - 1958 Heinz Zemanek: expresses doubts about goto at pre-ALGOL meeting.
  - 1968 Edsgar Dijkstra: ``GOTO Considered Harmful''
  - 1974 Don Knuth: ``Structured Programming with go to statements''
  - 1987 Frank Rubin: `` 'GOTO Considered Harmful' Considered Harmful''
  - 1995 Java first major language with no goto statement.
]

#slide()[
#v(-10%)
  == "Motivation: Why add goto to Python?"
#v(10%)

It seemed like a good idea at the time...

#v(1em)
Also useful for:

 -  Translating goto-filled code to python
 -  Finite state machines
 -  Generating python code programmatically
 -  Breaking out of a nested loop
]

// #slide(title: "Motivation: An extract from Hamurabi.bas")[
#slide()[
#v(-20%)
  == Motivation: An extract from Hamurabi.bas

  #v(10%)
From David Ahl's _101 Basic Computer Games_, 1973

```json
320 PRINT "HOW MANY ACRES DO YOU WISH TO BUY";
321 INPUT Q: IF Q<0 THEN 850
322 IF Y*Q<=S THEN 330
323 GOSUB 710
324 GOTO 320
330 IF Q=0 THEN 340
331 A=A+Q: S=S-Y*Q: C=0
334 GOTO 400
```
//From David Ahl's _101 Basic Computer Games_, 1973
]

#slide()[
  #v(-20%)
  == Motivation: State machines
  #align(center)[
  #image("doors.dot.png")
]
]

#slide()[
  #v(-20%)
  == Mechanism: Python bytecode manipulation

  Within a function that uses goto:

  + (Mis)use attribute access for labels and goto. e.g. *`label .found`* #pause
  + Extract a function's bytecode #pause
  + Replace bytecode for *`goto .found`* with relative jump to label #pause
  + Detect/Avoid/Mitigate various possible Bad Things #pause
  + Replace the function's bytecode with the new goto-ified bytecode
]

#slide()[
  #v(-25%)
  == Mechanism: Simple example function
  #set text(size: 23pt)

  ```py3
from goto import goto

@goto                         # the goto decorator rewrites bytecode
def find_value(rectangle, n):
    for line in rectangle:
        for value in line:
            if value == n:
                rval = "found
                goto .found   # jump down to label .found
    rval = "not found"
    label .found              # a no-op at runtime
    # ... other code here ...
    return rval
  ```
]

#slide()[
   #v(-25%)
  == Mechanism: Possible problems

- At for-loop start, python pushes an iterator.
  Pop when jumping out of a loop
- Jumps >255 instructions require *`EXTENDED_ARG`* opcode
- Illegal:

  - Jump into a for-loop.
  - Jump into/out of *`try`*, *`except`*, *`finally`*, *`with`*
  - Multiple identical labels (or missing label)
  - Jump out of nested for loops more than 10 deep.
  - Very long jumps (65536 bytecodes)
]

#slide()[
   #v(-20%)
  == Measurement: Non-trivial state machine

  Recognises valid sum expression of floating point numbers
   #align(center)[
  #image("fp_sum_expr.png")
]

Example: *`123.45+60e+3+123.45e-67+12`*
]

#slide()[
  #v(-10%)
  == Measurement: Possible implementations

  Compare:

 + Use existing *`python-statemachine`* library
 + Use *`for`* loop with a *`match`* statement
 + Use a regular expression: \
        *`\d+(\.\d+)?(e[+-]\d+)?(\+\d+(\.\d+)?(e[+-]\d+)?)*\$'`*
 + Use gotos for transition between states

 Using valid 30,000 character strings
]

#slide()[
  #v(-10%)
  == Measurement: Results

  #v(10%)

  #table(
    columns: (auto, auto, auto),
    rows: (50pt, 50pt, 50pt, 50pt, 50pt),
    align: (x,y) => (left, right, right).at(x),
    // inset: 10%,
    [*Method*], [*Recognition time*],[*Speed vs goto*],
    [python-statemachine], [504ms], [180x],
    [*`for`* loop + *`match`*], [21ms], [7.5x],
    [regular expression], [3.1ms], [1.1x],
    [goto], [2.8ms], [1x]
  )
]

#slide()[
  #v(-15%)
  == Musings

  #v(10%)

 - Bytecode rewriting is powerful #pause
 - Non-standard: CPython only #pause
 - Fast but fragile: Bytecode can change between python versions #pause
 - Goto: Historic re-enactment and fast state machines #pause
 - Don't use in production! #pause

 The End. Any questions?
]