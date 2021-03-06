
#include <gtest/gtest.h>
#include "test_util.hpp"
#include "graph_client.hpp"

#include <map>

using namespace jubatus::client;
static const int PORT = 65431;

namespace jubatus {

  typedef uint64_t edge_id_t;
  typedef std::string node_id;
  typedef int centrality_type;

}

namespace {

  class graph_test : public ::testing::Test {
  protected:
    pid_t child_;

    graph_test(){
      child_ = fork_process("graph", PORT, "./test_input/config.graph.json");
    };
    virtual ~graph_test(){
      kill_process(child_);
    };
    virtual void restart_process(){

      kill_process(this->child_);
      this->child_ = fork_process("graph", PORT, "./test_input/config.graph.json");
    };
  };

TEST_F(graph_test, simple){
  
  jubatus::node_id nid = "0";
  jubatus::node_id nid0 = "1";
  graph c("localhost", PORT, 10);
  {
    c.clear("");
    nid = c.create_node("");
    nid0 = c.create_node("");

    c.get_config("");
  };
  jubatus::edge_id_t eid = 0;
  {
    jubatus::property p;
    p["hoge"] = "huga";
    p["name"] = "test0";
    c.update_node("", nid, p);
    p["name"] = "testoooo";
    c.update_node("", nid0, p);

    p["name"] = "edge_name_hoge";
    jubatus::edge_info ei;
    ei.src = nid;
    ei.tgt = nid0;
    ei.p = p;
    eid = c.create_edge("", nid, ei);
    c.create_edge("", nid0, ei); //TODO: do we need this? release?
  }
  {
    c.save("", "test");
    c.clear("");
    c.load("", "test");
  }
  {
    jubatus::node_info i = c.get_node("", nid);
    ASSERT_EQ(0u, i.in_edges.size());
    EXPECT_EQ(2u, i.out_edges.size());  // FIXME: is this correct?(before 1)
    ASSERT_EQ("huga", i.p["hoge"]);
    ASSERT_EQ("test0", i.p["name"]);
  }
  {
    // eid = 0 , is nothing
    jubatus::edge_info i = c.get_edge("", nid, eid);
    ASSERT_EQ(nid , i.src);
    ASSERT_EQ(nid0, i.tgt);
    ASSERT_EQ(2u,   i.p.size());
    ASSERT_EQ("edge_name_hoge", i.p["name"]);
  }

  {
    c.get_status("");
    c.update_index("");
  }

  {
    jubatus::preset_query q;
    c.add_centrality_query("", q);
    c.update_index(""); // call manually in standalone mode
    double cent = c.get_centrality("", nid, 0, q);
    ASSERT_LT(0.0, cent);
  }

  {
    jubatus::shortest_path_req req;
    req.src = nid;
    req.tgt = nid0;
    { // FIXME
      req.max_hop = 10;
      jubatus::preset_query q;
      //c.add_shortest_path_query("", q);
      //std::vector<jubatus::node_id> path = c.get_shortest_path("", req);
      //ASSERT_EQ(1u, path.size());
    }
    {
      req.max_hop = 0;
      jubatus::preset_query q;
      c.add_shortest_path_query("", q);
      std::vector<jubatus::node_id> path = c.get_shortest_path("", req);
      ASSERT_EQ(0u, path.size());
    }
  }

  {
    jubatus::preset_query q;
    c.add_centrality_query("", q);
    c.add_shortest_path_query("", q);
    c.remove_centrality_query("", q);
    c.remove_shortest_path_query("", q);
  }
}

}
