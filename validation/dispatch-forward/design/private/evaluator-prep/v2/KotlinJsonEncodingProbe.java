import java.nio.charset.StandardCharsets;
import java.util.Base64;
import kotlinx.serialization.json.*;
public class KotlinJsonEncodingProbe {
  public static void main(String[] args) throws Exception {
    String input=new String(System.in.readAllBytes(),StandardCharsets.UTF_8);
    JsonObject root=(JsonObject)Json.Default.parseToJsonElement(input);
    JsonArray vectors=(JsonArray)root.get("vectors");
    System.out.print("{\"version\":1,\"producer\":\"kotlinx.serialization.json.JsonObject.toString\",\"results\":[");
    boolean first=true;
    for(JsonElement item:vectors) {
      JsonObject vector=(JsonObject)item;
      if(!first)System.out.print(",");
      first=false;
      String id=vector.get("id").toString();
      String encoded=Base64.getEncoder().encodeToString(vector.get("model").toString().getBytes(StandardCharsets.UTF_8));
      System.out.print("{\"id\":"+id+",\"utf8_base64\":\""+encoded+"\"}");
    }
    System.out.print("]}");
  }
}
