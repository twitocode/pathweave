import asyncio
import json
import re
import httpx

# School ID for McMaster University
SCHOOL_ID_B64 = "U2Nob29sLTE0NDA="
GRAPHQL_URL = "https://www.ratemyprofessors.com/graphql"
HEADERS = {
    "Authorization": "Basic dGVzdDp0ZXN0",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
}

# Semaphore to limit concurrency
MAX_CONCURRENT_TEACHERS = 10


async def get_all_teachers():
    teachers = []
    has_next_page = True
    cursor = ""

    query = """
    query TeacherSearchPaginationQuery(
      $count: Int!
      $cursor: String
      $query: TeacherSearchQuery!
    ) {
      newSearch {
        teachers(query: $query, first: $count, after: $cursor) {
          edges {
            node {
              id
              firstName
              lastName
              avgRating
              avgDifficulty
              numRatings
              department
            }
          }
          pageInfo {
            hasNextPage
            endCursor
          }
        }
      }
    }
    """

    async with httpx.AsyncClient(headers=HEADERS, timeout=30.0) as client:
        while has_next_page:
            variables = {
                "count": 100,
                "cursor": cursor,
                "query": {"text": "", "schoolID": SCHOOL_ID_B64},
            }

            try:
                response = await client.post(
                    GRAPHQL_URL, json={"query": query, "variables": variables}
                )
                data = response.json()

                edges = data["data"]["newSearch"]["teachers"]["edges"]
                for edge in edges:
                    teachers.append(edge["node"])

                page_info = data["data"]["newSearch"]["teachers"]["pageInfo"]
                has_next_page = page_info["hasNextPage"]
                cursor = page_info["endCursor"]

                print(f"Fetched {len(teachers)} teachers...", end="\r")
            except Exception as e:
                print(f"\n[Error] Failed to fetch teachers: {e}")
                break

    print(f"\nTotal teachers found: {len(teachers)}")
    return teachers


async def get_teacher_courses(client, teacher, semaphore):
    async with semaphore:
        query = """
        query TeacherRatingsPageQuery($id: ID!) {
          node(id: $id) {
            ... on Teacher {
              ratings(first: 100) {
                edges {
                  node {
                    class
                  }
                }
              }
            }
          }
        }
        """

        try:
            response = await client.post(
                GRAPHQL_URL, json={"query": query, "variables": {"id": teacher["id"]}}
            )
            data = response.json()

            ratings = data["data"]["node"]["ratings"]["edges"]
            # Extract unique course codes
            courses = set()
            for r in ratings:
                c = r["node"]["class"]
                if c:
                    courses.add(
                        c.upper().replace(" ", "")
                    )  # Normalize to compact uppercase

            return {
                "id": teacher["id"],
                "name": f"{teacher['firstName']} {teacher['lastName']}",
                "avgRating": teacher["avgRating"],
                "avgDifficulty": teacher["avgDifficulty"],
                "numRatings": teacher["numRatings"],
                "department": teacher["department"],
                "courses": list(courses),
            }
        except Exception as e:
            # print(f"\n[Error] Failed for {teacher['firstName']} {teacher['lastName']}: {e}")
            return None


async def main():
    teachers_basic = await get_all_teachers()

    # For efficiency in this demo, let's only do the first 500 teachers with most ratings
    # or just all if it's fast enough. Let's try all with a higher semaphore.
    # Actually, 2288 is a lot of requests. Let's filter to those with at least 1 rating.
    active_teachers = [t for t in teachers_basic if t["numRatings"] > 0]
    print(f"Active teachers (with ratings): {len(active_teachers)}")

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_TEACHERS)

    async with httpx.AsyncClient(headers=HEADERS, timeout=30.0) as client:
        tasks = [get_teacher_courses(client, t, semaphore) for t in active_teachers]

        print("Fetching course details for each teacher...")
        detailed_teachers = await asyncio.gather(*tasks)

    valid_results = [t for t in detailed_teachers if t is not None]

    # Create the mapping: Course -> [Professors]
    course_to_profs = {}
    for t in valid_results:
        for c in t["courses"]:
            if c not in course_to_profs:
                course_to_profs[c] = []
            course_to_profs[c].append(
                {
                    "name": t["name"],
                    "avgRating": t["avgRating"],
                    "avgDifficulty": t["avgDifficulty"],
                    "numRatings": t["numRatings"],
                    "department": t["department"],
                    "rmpId": t["id"],
                }
            )

    with open("data/rmp_data.json", "w") as f:
        json.dump(
            {"professors": valid_results, "course_mapping": course_to_profs},
            f,
            indent=2,
        )

    print(f"\nSuccess! Scraped {len(valid_results)} professors.")
    print(f"Data saved to rmp_data.json")


if __name__ == "__main__":
    asyncio.run(main())
