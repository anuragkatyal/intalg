var ptx_lunr_search_style = "textbook";
var ptx_lunr_docs = [
{
  "id": "sec-1_1",
  "level": "1",
  "url": "sec-1_1.html",
  "type": "Section",
  "number": "1.1",
  "title": "Fractions and Order of Operations",
  "body": " Fractions and Order of Operations   "
},
{
  "id": "sec-1_2",
  "level": "1",
  "url": "sec-1_2.html",
  "type": "Section",
  "number": "1.2",
  "title": "What is a solution?",
  "body": " What is a solution?   "
},
{
  "id": "sec-1_3",
  "level": "1",
  "url": "sec-1_3.html",
  "type": "Section",
  "number": "1.3",
  "title": "Solving Linear Equations",
  "body": " Solving Linear Equations   "
},
{
  "id": "sec-1_4",
  "level": "1",
  "url": "sec-1_4.html",
  "type": "Section",
  "number": "1.4",
  "title": "The Last of Us",
  "body": " The Last of Us   "
},
{
  "id": "sec-1_5",
  "level": "1",
  "url": "sec-1_5.html",
  "type": "Section",
  "number": "1.5",
  "title": "Linear Jargon and Graphs",
  "body": " Linear Jargon and Graphs   "
},
{
  "id": "sec-1_6",
  "level": "1",
  "url": "sec-1_6.html",
  "type": "Section",
  "number": "1.6",
  "title": "Slope",
  "body": " Slope   "
},
{
  "id": "sec-1_7",
  "level": "1",
  "url": "sec-1_7.html",
  "type": "Section",
  "number": "1.7",
  "title": "Slope Intercept Form",
  "body": " Slope Intercept Form   "
},
{
  "id": "sec-1_8",
  "level": "1",
  "url": "sec-1_8.html",
  "type": "Section",
  "number": "1.8",
  "title": "Point Slope Form",
  "body": " Point Slope Form   "
},
{
  "id": "sec-1_9",
  "level": "1",
  "url": "sec-1_9.html",
  "type": "Section",
  "number": "1.9",
  "title": "Parallel and Perpendicular Lines",
  "body": " Parallel and Perpendicular Lines   "
},
{
  "id": "sec-1_10",
  "level": "1",
  "url": "sec-1_10.html",
  "type": "Section",
  "number": "1.10",
  "title": "System of Linear Equations",
  "body": " System of Linear Equations   "
},
{
  "id": "sec-2_1",
  "level": "1",
  "url": "sec-2_1.html",
  "type": "Section",
  "number": "2.1",
  "title": "Introduction to Inequalities",
  "body": " Introduction to Inequalities  asdgsd  "
},
{
  "id": "sec-3_1",
  "level": "1",
  "url": "sec-3_1.html",
  "type": "Section",
  "number": "3.1",
  "title": "Introduction to Inequalities",
  "body": " Introduction to Inequalities  asdgsd  "
},
{
  "id": "sec-4_1",
  "level": "1",
  "url": "sec-4_1.html",
  "type": "Section",
  "number": "4.1",
  "title": "Introduction to Inequalities",
  "body": " Introduction to Inequalities  asdgsd  "
},
{
  "id": "sec-5_1",
  "level": "1",
  "url": "sec-5_1.html",
  "type": "Section",
  "number": "5.1",
  "title": "Introduction to Inequalities",
  "body": " Introduction to Inequalities  asdgsd  "
}
]

var ptx_lunr_idx = lunr(function () {
  this.ref('id')
  this.field('title')
  this.field('body')
  this.metadataWhitelist = ['position']

  ptx_lunr_docs.forEach(function (doc) {
    this.add(doc)
  }, this)
})
