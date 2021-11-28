
import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.TokenStream;
import org.apache.lucene.analysis.Tokenizer;
import org.apache.lucene.analysis.ar.ArabicLetterTokenizer;
import org.apache.lucene.analysis.ar.ArabicNormalizationFilter;
import org.apache.lucene.analysis.core.LowerCaseFilter;
import org.apache.lucene.analysis.core.StopAnalyzer;
import org.apache.lucene.analysis.core.StopFilter;
import org.apache.lucene.analysis.fa.PersianAnalyzer;
import org.apache.lucene.analysis.fa.PersianCharFilter;
import org.apache.lucene.analysis.fa.PersianNormalizationFilter;
import org.apache.lucene.analysis.fa.PersianNormalizer;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.analysis.standard.StandardFilter;
import org.apache.lucene.analysis.tokenattributes.CharTermAttribute;
import org.apache.lucene.analysis.util.CharArraySet;
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.document.StringField;
import org.apache.lucene.document.TextField;
import org.apache.lucene.index.*;
import org.apache.lucene.queryparser.classic.QueryParser;
import org.apache.lucene.search.*;
import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.util.Version;
import org.tartarus.snowball.ext.PorterStemmer;

import java.io.*;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Objects;

import static org.apache.lucene.util.Version.LUCENE_40;

/**
 * This terminal application creates an Apache Lucene index in a folder and adds files into this index
 * based on the input of the user.
 */
public class TextFileIndexer {
    private static PersianAnalyzer analyzer = new PersianAnalyzer(LUCENE_40, PersianAnalyzer.getDefaultStopSet());

    private IndexWriter writer;
    private ArrayList<File> queue = new ArrayList<File>();


    public static void main(String[] args) throws IOException {
        System.out.println("all stop word that stored in persian analyser deleted");

        System.out.println("please wait until making index using files inside hamshahri directory");
        String indexLocation = "sources/index"   ;
        TextFileIndexer indexer = new TextFileIndexer(indexLocation);
        indexer.indexFileOrDirectory("sources/hamshahri/Test");
        indexer.indexFileOrDirectory("sources/hamshahri/Train");

        indexer.closeIndex();


        IndexReader reader = DirectoryReader.open(FSDirectory.open(new File(indexLocation)));
        IndexSearcher searcher = new IndexSearcher(reader);
        String line = "";
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));

        outer:while (true) {
            try {
                System.out.println("Enter the search query (q=quit, $=end of file):");
                boolean stop = false, hasDate = false, hasCategory = false, hasTitle = false;
                Query dateQuery, categoryQuery, titleQuery, textQuery;
                BooleanClause dataClause = null, categoryClause = null, titleClause = null, textClause = null;
                StringBuilder text = new StringBuilder();
                    while (true){
                    line = br.readLine();
                    if (line.equalsIgnoreCase("q"))
                        break outer;
                    if (line.equalsIgnoreCase("$"))
                        break ;
                        if (!stop && line.contains("date")) {
                            hasDate = true;
                            continue;
                        }
                        else if (!stop && line.contains("category")) {
                            hasCategory = true;
                            continue;
                        }
                        else if (!stop && line.contains("title")) {
                            hasTitle = true;
                            continue;
                        }
                        else if (!stop && line.contains("text")) {
                            stop = true;
                            continue;
                        }

                        if (hasDate) {
                            dateQuery = new TermQuery(new Term("date", line));
                            dataClause = new BooleanClause(dateQuery, BooleanClause.Occur.MUST);
                            hasDate = false;
                        }
                        else if (hasCategory) {
                            categoryQuery = new TermQuery(new Term("category", line));
                            categoryClause = new BooleanClause(categoryQuery, BooleanClause.Occur.MUST);
                            hasCategory = false;
                        }
                        else if (hasTitle) {
                            titleQuery = new TermQuery(new Term("title", line));
                            titleClause = new BooleanClause(titleQuery, BooleanClause.Occur.MUST);
                            hasTitle = false;
                        }
                        else
                            text.append(line);
                    }
                    if (!Objects.equals(text.toString(), "")) {
                        String textString = stemmingQuery(text.toString());
                        textQuery = new TermQuery(new Term("text", textString));
                        textClause = new BooleanClause(textQuery, BooleanClause.Occur.MUST);
                    }

                    BooleanQuery booleanQuery = new BooleanQuery();
                    if (dataClause != null)
                        booleanQuery.add(dataClause);
                    if (categoryClause != null)
                        booleanQuery.add(categoryClause);
                    if (titleClause != null)
                        booleanQuery.add(titleClause);
                    if (textClause != null)
                        booleanQuery.add(textClause);

                    String str = booleanQuery.toString().replace('\t', '\u200c');
                    Query query = new QueryParser(LUCENE_40, "", analyzer).parse(str);

//                    TopScoreDocCollector collector = TopScoreDocCollector.create(10, true);
                    int collector = 10;
                    TopDocs docs = searcher.search(query, collector);
//                    searcher.search(query, collector);
//                    ScoreDoc[] topDocs = collector.topDocs().scoreDocs;
                    ScoreDoc[] topDocs = docs.scoreDocs;
                    // 4. display results
                    System.out.println("Found " + topDocs.length + " hits.");

                    for(int i=0 ; i < Math.min(10, topDocs.length) ; ++i) {
                        int docId = topDocs[i].doc;
                        Document d = searcher.doc(docId);
                        System.out.println((i + 1) + ". " + d.get("path") + " score=" + topDocs[i].score);
                    }

            } catch (Exception e) {
                System.out.println("Error searching " + e.getMessage() + "error location : " + e.getLocalizedMessage());
            }
        }

    }

    private static String stemmingQuery(String text) throws IOException {
        Tokenizer tokenizer = new ArabicLetterTokenizer(LUCENE_40, new StringReader(text));
        final StandardFilter standardFilter = new StandardFilter(LUCENE_40, tokenizer);
        final StopFilter stopFilter = new StopFilter(LUCENE_40, standardFilter, PersianAnalyzer.getDefaultStopSet());

        final CharTermAttribute charTermAttribute = tokenizer.addAttribute(CharTermAttribute.class);

        stopFilter.reset();
        StringBuilder finalText = new StringBuilder();
        while(stopFilter.incrementToken()) {
            final String token = charTermAttribute.toString();
            if ( !PersianAnalyzer.getDefaultStopSet().contains(token))
            {
                PersianNormalizer persianNormalizer = new PersianNormalizer();
                persianNormalizer.normalize(token.toCharArray(), token.toCharArray().length);
                finalText.append(token+'\t');
            }

        }

        Reader reader = new PersianCharFilter(new StringReader(finalText.toString()));
        return convertReaderToString(reader);
    }
    private static String  convertReaderToString(Reader reader)
            throws IOException {
        int intValueOfChar;
        StringBuilder targetString = new StringBuilder();
        while ((intValueOfChar = reader.read()) != -1) {
            targetString.append((char) intValueOfChar);
        }
        reader.close();
        return targetString.toString();
    }

    /**
     * Constructor
     * @param indexDir the name of the folder in which the index should be created
     * @throws java.io.IOException when exception creating index.
     */
    TextFileIndexer(String indexDir) throws IOException {
        // the boolean true parameter means to create a new index everytime,
        // potentially overwriting any existing files there.
        FSDirectory dir = FSDirectory.open(new File(indexDir));


        IndexWriterConfig config = new IndexWriterConfig(LUCENE_40, analyzer);

        writer = new IndexWriter(dir, config);
    }

    /**
     * Indexes a file or directory
     * @param fileName the name of a text file or a folder we wish to add to the index
     * @throws java.io.IOException when exception
     */
    public void indexFileOrDirectory(String fileName) throws IOException {
        //===================================================
        //gets the list of files in a folder (if user has submitted
        //the name of a folder) or gets a single file name (is user
        //has submitted only the file name) 
        //===================================================
        addFiles(new File(fileName));

        int originalNumDocs = writer.numDocs();
        for (File f : queue) {
            FileReader fr = null;
            try {
                Document doc = new Document();

                //===================================================
                // add contents of file
                //===================================================
                fr = new FileReader(f);
                BufferedReader br = new BufferedReader(fr);
                String line = null;
                boolean stop = false, hasDate = false, hasCategory = false, hasTitle = false;
                StringBuilder text = new StringBuilder();
                while ((line = br.readLine()) != null) {
                    if (!stop && line.contains("date")){
                        hasDate = true;
                        continue;
                    }
                    else if (!stop && line.contains("category")) {
                        hasCategory = true;
                        continue;
                    }
                    else if (!stop && line.contains("title")) {
                        hasTitle = true;
                        continue;
                    }
                    else if (!stop && line.contains("text")){
                        stop = true;
                        continue;
                    }

                    if (hasDate){
                        doc.add(new TextField("date", line, Field.Store.YES));
                        hasDate = false;
                    }
                    else if (hasCategory){
                        doc.add(new TextField("category", line, Field.Store.YES));
                        hasCategory = false;
                    }
                    else if (hasTitle){
                        doc.add(new TextField("title", line, Field.Store.YES));
                        hasTitle = false;
                    }
                    else
                        text.append(line);
                }

                doc.add(new TextField("text", text.toString(), Field.Store.YES));
                doc.add(new StringField("path", f.getPath(), Field.Store.YES));
                doc.add(new StringField("filename", f.getName(), Field.Store.YES));

                writer.addDocument(doc);
//                System.out.println("Added: " + f);
            } catch (Exception e) {
                System.out.println("Could not add: " + f);
            } finally {
                fr.close();
            }
        }

        int newNumDocs = writer.numDocs();
        System.out.println("************************");
        System.out.println((newNumDocs - originalNumDocs) + " documents added.");
        System.out.println("************************");

        queue.clear();
    }

    private void addFiles(File file) {

        if (!file.exists()) {
            System.out.println(file + " does not exist.");
        }
        if (file.isDirectory()) {
            for (File f : file.listFiles()) {
                addFiles(f);
            }
        } else {
            String filename = file.getName().toLowerCase();
            //===================================================
            // Only index text files
            //===================================================
            if (filename.endsWith(".htm") || filename.endsWith(".html") ||
                    filename.endsWith(".xml") || filename.endsWith(".txt")) {
                queue.add(file);
            } else {
                System.out.println("Skipped " + filename);
            }
        }
    }

    /**
     * Close the index.
     * @throws java.io.IOException when exception closing
     */
    public void closeIndex() throws IOException {
        writer.close();
    }
}

 
